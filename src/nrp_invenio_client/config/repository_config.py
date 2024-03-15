import dataclasses
import typing

if typing.TYPE_CHECKING:
    pass


@dataclasses.dataclass
class RepositoryConfig:
    """Configuration of the repository"""

    alias: str
    url: str
    token: typing.Optional[str] = None
    verify: bool | str = True
    retry_count: int = 10
    retry_interval: int = 10
    record_aliases: typing.Dict[str, typing.List[str] | str] = dataclasses.field(
        default_factory=dict
    )
