import re
from collections.abc import Iterable, Sequence
from functools import cache
from pathlib import Path
from typing import Optional

from oci.core import ComputeClient, VirtualNetworkClient
from oci.core.models import (
    CreateVnicDetails,
    Image,
    Instance,
    InstanceSourceViaImageDetails,
    LaunchInstanceDetails,
    LaunchInstanceShapeConfigDetails,
    Shape,
    Subnet,
    UpdateInstanceDetails,
    UpdateInstanceShapeConfigDetails,
)
from oci.identity import IdentityClient
from oci.identity.models import AvailabilityDomain
from oci.limits import LimitsClient

from get_oracle_a1.config import OCIUser
from get_oracle_a1.models import IncreaseStep, ResourceLimit

TARGET_SHAPE = 'VM.Standard.A1.Flex'


def find_target_instance(oci_user: OCIUser, display_name: str) -> Optional[Instance]:
    client = ComputeClient(config=oci_user.config)
    list_query = client.list_instances(oci_user.compartment_id)

    instance: Instance
    for instance in list_query.data:
        if instance.display_name == display_name and instance.lifecycle_state not in (
            Instance.LIFECYCLE_STATE_TERMINATING,
            Instance.LIFECYCLE_STATE_TERMINATED,
        ):
            return instance

    return None


def get_instance(oci_user: OCIUser, ocid: str) -> Instance:
    client = ComputeClient(config=oci_user.config)
    return client.get_instance(instance_id=ocid).data


@cache
def list_availability_domain(oci_user: OCIUser) -> Sequence[AvailabilityDomain]:
    client = IdentityClient(oci_user.config)
    return client.list_availability_domains(oci_user.compartment_id).data


@cache
def get_a1_res_limit(oci_user: OCIUser, availability_domain: str) -> ResourceLimit:
    client = LimitsClient(config=oci_user.config)
    ocpu_res = client.list_limit_values(
        compartment_id=oci_user.compartment_id,
        service_name='compute',
        name='standard-a1-core-count',
        availability_domain=availability_domain,
    ).data
    if len(ocpu_res) != 1:
        raise RuntimeError('A1 is not available')
    memory_res = client.list_limit_values(
        compartment_id=oci_user.compartment_id,
        service_name='compute',
        name='standard-a1-memory-count',
        availability_domain=availability_domain,
    ).data
    if len(memory_res) != 1:
        raise RuntimeError('A1 is not available')

    return ResourceLimit(
        ocpu=ocpu_res[0].value,
        memory=memory_res[0].value,
    )


def increase_resource(oci_user: OCIUser, instance: Instance, step: IncreaseStep) -> None:
    client = ComputeClient(config=oci_user.config)
    client.update_instance(
        instance_id=instance.id,
        update_instance_details=UpdateInstanceDetails(
            shape_config=UpdateInstanceShapeConfigDetails(
                ocpus=step.ocpu,
                memory_in_gbs=step.memory,
            )
        ),
    )


@cache
def check_a1_available(oci_user: OCIUser, availability_domain: str, shape: str = TARGET_SHAPE) -> bool:
    return find_target_shape(oci_user=oci_user, shape=shape, availability_domain=availability_domain) is not None


@cache
def find_target_shape(oci_user: OCIUser, shape: str, availability_domain: str) -> Optional[Shape]:
    client = ComputeClient(config=oci_user.config)
    s: Shape
    for s in client.list_shapes(oci_user.compartment_id, availability_domain=availability_domain).data:
        if s.shape == shape:
            return s
    return None


def calc_next_increase_step(
    oci_user: OCIUser, instance: Instance, target_ocpu: int, target_memory: int, incremental: bool, _shape: str = TARGET_SHAPE
) -> IncreaseStep:
    shape = find_target_shape(oci_user=oci_user, shape=_shape, availability_domain=instance.availability_domain)
    if shape is None:
        raise RuntimeError(f'Failed to find shape {_shape or TARGET_SHAPE}')

    resource_limit = get_a1_res_limit(oci_user, instance.availability_domain)

    if not incremental:
        return IncreaseStep(
            ocpu=min(resource_limit.ocpu, target_ocpu), memory=min(resource_limit.memory, target_memory)
        )

    base_ocpu_step = shape.ocpu_options.min
    base_memory_step = shape.memory_options.default_per_ocpu_in_g_bs * base_ocpu_step

    return IncreaseStep(
        ocpu=min(instance.shape_config.ocpus + base_ocpu_step, resource_limit.ocpu, target_ocpu),
        memory=min(
            instance.shape_config.memory_in_gbs + base_memory_step,
            resource_limit.memory,
            target_memory,
        ),
    )


def verify_instance_for_increasing(instance: Instance, resource_limit: ResourceLimit, shape: str = TARGET_SHAPE) -> None:
    if instance.shape != shape:
        raise ValueError(f'{instance.shape} is not {shape}')

    if (
        instance.shape_config.ocpus >= resource_limit.ocpu
        and instance.shape_config.memory_in_gbs >= resource_limit.memory
    ):
        # TODO: custom exception
        raise ValueError('No room for resource extending')


def get_image(oci_user: OCIUser, os_name: str, os_version: Optional[str], shape: str = TARGET_SHAPE) -> Optional[list[Image]]:
    client = ComputeClient(config=oci_user.config)

    # OCI's operating_system_version field is always a plain number like
    # "22.04" - "Minimal"/"aarch64" only exist in the image's display name,
    # not this field. Extract just the number for the API call, and treat
    # "minimal" in the input separately as a display-name filter below.
    raw_version = (os_version or '').strip()
    wants_minimal = 'minimal' in raw_version.lower()
    match = re.match(r'^\d+(?:\.\d+)*', raw_version)
    normalized_version = match.group(0) if match else (os_version or None)

    images: Sequence[Image] = sorted(
        client.list_images(
            oci_user.compartment_id,
            shape=shape,
            operating_system=os_name,
            operating_system_version=normalized_version,
        ).data,
        key=lambda i: i.operating_system_version,
        reverse=True,
    )

    # Multiple images can share the same operating_system_version (a
    # "Minimal" build and the full build both report "22.04") - display
    # name is the only place that tells them apart.
    if wants_minimal:
        images = [i for i in images if 'minimal' in i.display_name.lower()]
    else:
        images = [i for i in images if 'minimal' not in i.display_name.lower()]

    if len(images) == 0:
        return None
    else:
        return images


def create_a1(
    oci_user: OCIUser,
    availability_domain: str,
    image_id: str,
    target_ocpu: int,
    target_memory: int,
    display_name: str,
    subnet_id: str,
    boot_volume_size: Optional[float],
    ssh_authorized_keys: Path,
    shape: str = TARGET_SHAPE,
) -> Instance:
    client = ComputeClient(config=oci_user.config)
    return client.launch_instance(
        LaunchInstanceDetails(
            display_name=display_name,
            compartment_id=oci_user.compartment_id,
            shape=shape,
            shape_config=LaunchInstanceShapeConfigDetails(
                ocpus=target_ocpu,
                memory_in_gbs=target_memory,
            ),
            availability_domain=availability_domain,
            create_vnic_details=CreateVnicDetails(
                subnet_id=subnet_id,
                hostname_label=display_name,
            ),
            source_details=InstanceSourceViaImageDetails(
                image_id=image_id,
                boot_volume_size_in_gbs=boot_volume_size,
            ),
            metadata=dict(
                ssh_authorized_keys=ssh_authorized_keys.read_text(),
            ),
            is_pv_encryption_in_transit_enabled=True,
            # launch_options=LaunchOptions(
            #     boot_volume_type=LaunchOptions.BOOT_VOLUME_TYPE_ISCSI,
            #     network_type=LaunchOptions.NETWORK_TYPE_VFIO,
            # ),
        )
    ).data


def list_shapes(oci_user: OCIUser, availability_domain: str) -> Sequence[Shape]:
    client = ComputeClient(config=oci_user.config)
    return client.list_shapes(oci_user.compartment_id, availability_domain=availability_domain).data


def group_shape_series(shapes: Iterable[Shape]) -> dict[str, list[str]]:
    """Group VM shape names into {series: [full shape name, ...]}.

    OCI shape names look like 'VM.Standard.A1.Flex' or 'VM.DenseIO.E4.Flex'.
    'series' here is the second dot-segment ('Standard', 'DenseIO', ...).
    Bare-metal ('BM.*') shapes are dropped - this dashboard is VM-only.
    """
    series_map: dict[str, list[str]] = {}
    for s in shapes:
        parts = s.shape.split('.')
        if len(parts) < 2 or parts[0] != 'VM':
            continue
        series = parts[1]
        names = series_map.setdefault(series, [])
        if s.shape not in names:
            names.append(s.shape)
    return series_map


def list_images_for_shape(oci_user: OCIUser, shape: str) -> Sequence[Image]:
    """All images compatible with a shape, no OS name/version filter -
    the caller (dashboard) groups/filters these client-side."""
    client = ComputeClient(config=oci_user.config)
    return client.list_images(oci_user.compartment_id, shape=shape).data


def list_available_subnet(oci_user: OCIUser) -> Iterable[Subnet]:
    client = VirtualNetworkClient(oci_user.config)
    subnet: Subnet
    for subnet in client.list_subnets(oci_user.compartment_id).data:
        if subnet.lifecycle_state == Subnet.LIFECYCLE_STATE_AVAILABLE:
            yield subnet
