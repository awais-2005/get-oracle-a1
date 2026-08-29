"""
Flask web dashboard for Oracle A1.Flex automation
Provides a UI to create, manage, and monitor instances
"""

import logging
import os
import tempfile
import configparser
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from flask import Flask, render_template, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash

from get_oracle_a1 import commands, config, helpers, usecases

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'change-me-in-production')

# Store execution logs in memory
execution_logs: Dict[str, list] = {}
execution_threads: Dict[str, threading.Thread] = {}


class ExecutionTracker:
    """Track execution status and logs"""

    def __init__(self, execution_id: str):
        self.execution_id = execution_id
        self.e = {} # Raise Exeptions
        self.logs = []
        self.status = 'running'  # running, success, failed
        self.start_time = datetime.now()
        self.end_time = None
        execution_logs[execution_id] = self

    def log(self, message: str, err_type: str = None):
        if message != "":
            self.logs.append({
                'timestamp': datetime.now().isoformat(),
                'message': message
            })
            logger.info(f"[{self.execution_id}] {message}")

        if err_type == None:
            return

        if err_type in self.e:
            e[err_type] += 1
        else:
            e[err_type] = 1

    def finish(self, status: str = 'success'):
        self.status = status
        self.end_time = datetime.now()

    def to_dict(self):
        return {
            'id': self.execution_id,
            'status': self.status,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'logs': self.logs,
            "e": self.e,
        }


def send_email(to_email: str, subject: str, body: str):
    """Send email notification"""
    try:
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        from_email = os.getenv('SMTP_USER')
        from_password = os.getenv('SMTP_PASSWORD')

        if not all([from_email, from_password]):
            logger.warning('Email credentials not configured. Skipping email send.')
            return False

        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(from_email, from_password)
            server.send_message(msg)

        logger.info(f'Email sent to {to_email}')
        return True
    except Exception as e:
        logger.error(f'Failed to send email: {e}')
        return False


def parse_oci_config(config_content: str, profile: str = 'DEFAULT') -> dict:
    """Parse an OCI CLI-style config file (ini format) into a dict."""
    parser = configparser.ConfigParser()
    parser.read_string(config_content)
    if profile not in parser:
        raise ValueError(f"Profile '[{profile}]' not found in the uploaded config file")
    section = parser[profile]
    missing = [k for k in ('user', 'fingerprint', 'tenancy') if k not in section]
    if missing:
        raise ValueError(f"Config file is missing: {', '.join(missing)}")
    return {
        'user': section['user'],
        'fingerprint': section['fingerprint'],
        'tenancy': section['tenancy'],
        'region': section.get('region', os.getenv('OCI_REGION', 'ap-hyderabad-1')),
    }

def create_instance_task(tracker: ExecutionTracker, cmd_data: dict, send_notification: bool):
    """Background task to create instance"""
    ssh_key_path: Optional[Path] = None
    try:
        tracker.log(f"Starting instance creation: {cmd_data['display_name']}")

        # Load OCI user credentials, in priority order:
        # 1) Config + key uploaded with this request
        # 2) Server environment variables
        oci_profile = cmd_data.get('profile', 'DEFAULT')
        config_content = cmd_data.get('oci_config_content')
        key_content = cmd_data.get('oci_private_key_content')

        if config_content and key_content:
            tracker.log("Using OCI config uploaded with this request")
            parsed = parse_oci_config(config_content, oci_profile)
            oci_user = config.OCIUser(
                user=parsed['user'],
                key_content=key_content,
                key_file=None,
                fingerprint=parsed['fingerprint'],
                tenancy=parsed['tenancy'],
                region=parsed['region'],
            )
        else:
            tracker.log("No config uploaded, using environment variables")
            oci_user = config.OCIUser(
                user=os.getenv('OCI_USER'),
                key_content=os.getenv('OCI_PRIVATE_KEY'),
                key_file=None,
                fingerprint=os.getenv('OCI_FINGERPRINT'),
                tenancy=os.getenv('OCI_TENANCY'),
                region=os.getenv('OCI_REGION', 'ap-hyderabad-1'),
            )

        # Prepare SSH key: the dashboard now uploads the key's content
        # directly (a filesystem path typed in the browser can't exist on
        # Render), so write it to a temp file since OCI needs a path to read.
        ssh_key_content = (cmd_data.get('ssh_authorized_keys') or '').strip()
        if not ssh_key_content:
            raise ValueError("SSH public key is required")
        if not ssh_key_content.startswith(('ssh-rsa', 'ssh-ed25519', 'ecdsa-sha2-')):
            raise ValueError("That doesn't look like an SSH public key (id_rsa.pub) — "
                              "make sure you uploaded the .pub file, not the private key")

        fd, tmp_path = tempfile.mkstemp(prefix='ssh_key_', suffix='.pub')
        with os.fdopen(fd, 'w') as f:
            f.write(ssh_key_content)
        ssh_key_path = Path(tmp_path)

        # Create command
        create_cmd = commands.CreateA1(
            availability_domain=cmd_data['availability_domain'],
            display_name=cmd_data['display_name'],
            os_name=cmd_data['os_name'],
            os_version=cmd_data.get('os_version'),
            subnet_id=cmd_data['subnet_id'],
            target_ocpu=int(cmd_data['ocpu']),
            target_memory=int(cmd_data['memory']),
            boot_volume_size=float(cmd_data.get('boot_volume_size', 100)),
            ssh_authorized_keys=ssh_key_path,
        )

        tracker.log(f"Command prepared: {create_cmd}")

        # Create instance
        usecases.create(create_cmd, oci_user, on_attempt=tracker.log)

        tracker.log(f"✓ Instance '{cmd_data['display_name']}' created successfully!")
        tracker.finish('success')

        # Send email notification
        if send_notification:
            email = cmd_data.get('notification_email')
            if email:
                send_email(
                    email,
                    f"Oracle Instance Created: {cmd_data['display_name']}",
                    f"Instance '{cmd_data['display_name']}' has been successfully created on Oracle Cloud.\n\n"
                    f"Configuration:\n"
                    f"- OCPUs: {cmd_data['ocpu']}\n"
                    f"- Memory: {cmd_data['memory']} GB\n"
                    f"- OS: {cmd_data['os_name']} {cmd_data.get('os_version', '')}\n"
                    f"- Availability Domain: {cmd_data['availability_domain']}\n"
                )

    except Exception as e:
        tracker.log(f"✗ Error: {str(e)}")
        tracker.finish('failed')
        logger.exception("Failed to create instance")
    finally:
        if ssh_key_path is not None:
            ssh_key_path.unlink(missing_ok=True)

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')


@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


@app.route('/api/create-instance', methods=['POST'])
def create_instance():
    """Create new instance"""
    try:
        data = request.json
        execution_id = f"create-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        tracker = ExecutionTracker(execution_id)

        # Start in background thread
        thread = threading.Thread(
            target=create_instance_task,
            args=(tracker, data, data.get('send_notification', False))
        )
        thread.daemon = True
        thread.start()
        execution_threads[execution_id] = thread

        return jsonify({
            'execution_id': execution_id,
            'status': 'started'
        })

    except Exception as e:
        logger.exception("Error starting instance creation")
        return jsonify({'error': str(e)}), 400


@app.route('/api/increase-resources', methods=['POST'])
def increase_resources():
    """Increase instance resources"""
    try:
        data = request.json
        execution_id = f"increase-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        tracker = ExecutionTracker(execution_id)
        tracker.log(f"Starting resource increase for instance: {data['display_name']}")

        # You can implement this similarly to create_instance_task
        tracker.log("Resource increase feature coming soon")
        tracker.finish('success')

        return jsonify({
            'execution_id': execution_id,
            'status': 'started'
        })

    except Exception as e:
        logger.exception("Error starting resource increase")
        return jsonify({'error': str(e)}), 400


@app.route('/api/executions')
def list_executions():
    """List all executions"""
    executions = [tracker.to_dict() for tracker in execution_logs.values()]
    # Sort by start time, newest first
    executions.sort(key=lambda x: x['start_time'])

    return jsonify(executions)


@app.route('/api/executions/<execution_id>')
def get_execution(execution_id: str):
    """Get execution details"""
    tracker = execution_logs.get(execution_id)
    if not tracker:
        return jsonify({'error': 'Execution not found'}), 404
    return jsonify(tracker.to_dict())


@app.route('/api/config')
def get_config():
    """Get available configuration options"""
    return jsonify({
        'regions': ['ap-hyderabad-1', 'us-phoenix-1', 'us-ashburn-1'],
        'os_options': [
            {'name': 'Canonical Ubuntu', 'versions': ['22.04', '20.04']},
            {'name': 'Oracle Linux', 'versions': ['9.0', '8.0']},
        ],
        'default_boot_volume': 100,
        'default_ocpu': 2,
        'default_memory': 12,
        'max_ocpu': 80,
        'max_memory': 480,
    })


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'production') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
