from typing import Optional

from pydantic import BaseModel, FilePath


class Command(BaseModel):
    class Config:
        allow_mutation = False
        orm_mode = True


class IncreaseResource(Command):
    instance_ocid: str
    target_ocpu: int
    target_memory: int
    incremental: bool


class CreateA1(Command):
    availability_domain: str
    display_name: str
    os_name: Optional[str]
    os_version: Optional[str]
    image_id: Optional[str]  # exact image OCID chosen in the dashboard; skips the name/version search when set
    shape: Optional[str]  # full shape name, e.g. 'VM.Standard.A1.Flex'; defaults to TARGET_SHAPE when unset
    subnet_id: Optional[str]
    target_ocpu: Optional[int]
    target_memory: Optional[int]
    boot_volume_size: Optional[float]
    ssh_authorized_keys: FilePath


class ListAvailabilityDomain(Command):
    pass


class ListAvailableSubnet(Command):
    pass
