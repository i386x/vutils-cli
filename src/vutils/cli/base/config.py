#
# File:    ./src/vutils/cli/base/config.py
# Author:  Jiří Kučera <sanczes AT gmail.com>
# Date:    2024-03-02 17:22:38 +0100
# Project: vutils-cli: Auxiliary library for writing CLI applications
#
# SPDX-License-Identifier: MIT
#
"""Configuration management."""

from typing import TYPE_CHECKING

from vutils.validator.schema import (
    KW_DEFINITIONS,
    KW_ENUM,
    KW_MINLENGTH,
    KW_PROPERTIES,
    KW_REF,
    KW_STRING,
    KW_TYPE,
    copy_and_check_schema,
    ensure_ref,
    get_description,
    new_object,
    new_ref,
    new_schema,
    validate,
)
from vutils.yaml.utils import getloc

from vutils.cli.base.errors import ApplicationError

if TYPE_CHECKING:
    from typing_extensions import TypeAlias

    from referencing.jsonschema import Schema
    from vutils.validator import JsonSchemaError, JsonSchemaSchemaError
    from vutils.validator.value import Location

    ConfigValueType: TypeAlias = "ConfigItem | ConfigType"
    ConfigType: TypeAlias = "dict[str, ConfigValueType]"
else:
    from vutils.validator.schema import JsonSchemaSchemaError

#: The ``key_type`` keyword
KW_KEY_TYPE: str = "key_type"
#: The ``empty`` keyword
KW_EMPTY: str = "empty"
#: The delimiter character that delimits path segments
PATH_DELIMITER: str = "/"


def to_parts(path: str) -> "list[str]":
    """
    Split :arg:`path` to the list of its segments.

    :param path: The path
    :return: the list of segments of :arg:`path`

    Empty segments are discarded.
    """
    return list(filter(None, (p.strip() for p in path.split(PATH_DELIMITER))))


def to_path(parts: "list[str]") -> str:
    """
    Make the path from :arg:`parts`.

    :param parts: The list of segments
    :return: the path made from :arg:`parts`
    """
    return PATH_DELIMITER.join(parts)


class ConfigError(ApplicationError):
    """Base class of all configuration errors."""

    #: The reason of an error
    reason: str

    __slots__ = ("reason",)

    def __init__(self, reason: str) -> None:
        """
        Initialize the error object.

        :param reason: The reason of this error
        """
        ApplicationError.__init__(self)
        self.reason = reason
        self.detail = f'reason="{self.reason}"'

    def __str__(self) -> str:
        """
        Get the error message.

        :return: the error message
        """
        return f"Config: {self.reason}"


class ConfigItemError(ConfigError):
    """Base class for configuration item errors."""

    __slots__ = ()

    def __init__(self, item: "ConfigItem", reason: str) -> None:
        """
        Initialize the error object.

        :param item: The configuration item
        :param reason: The reason of this error
        """
        ConfigError.__init__(self, f"{item.fqname}: {reason}")

    @staticmethod
    def make_report(reason: str, errors: "list[JsonSchemaError]") -> str:
        """
        Make an error report.

        :param reason: The reason of this error
        :param errors: The list of errors keeping more detailed information
            about the cause of this error
        :return: the error report

        Make a pretty-formatted error report starting with :arg:`reason` and
        listing all of :arg:`errors`.
        """
        report = reason
        if len(errors) > 0:
            report += ":"
        joiner = "\n  * " if len(errors) > 1 else " "
        parts: "list[str]" = [report]
        for error in errors:
            location = str(getloc(error.instance))
            spacer = ": " if location else ""
            parts.append(f"{location}{spacer}{error!s}")
        return joiner.join(parts)


class InvalidSchema(ConfigItemError):
    """Raised when a schema is not valid."""

    __slots__ = ()

    def __init__(
        self, item: "ConfigItem", error: "JsonSchemaSchemaError"
    ) -> None:
        """
        Initialize the error object.

        :param item: The configuration item
        :param error: The schema error
        """
        ConfigItemError.__init__(
            self, item, ConfigItemError.make_report("Invalid schema", [error])
        )


class InvalidValue(ConfigItemError):
    """Raised when a value is not valid."""

    __slots__ = ()

    def __init__(
        self, item: "ConfigItem", errors: "list[JsonSchemaError]"
    ) -> None:
        """
        Initialize the error object.

        :param item: The configuration item
        :param errors: The list of value validation errors
        """
        ConfigItemError.__init__(
            self, item, ConfigItemError.make_report("Invalid value", errors)
        )


class Origin:
    """Represent the origin of a value."""

    #: The detail about the origin
    detail: "str | Location | None"

    __slots__ = ("detail",)

    def __init__(self, detail: "str | Location | None" = None) -> None:
        """
        Initialize the value origin.

        :param detail: The detail about the origin
        """
        self.detail = detail

    def __repr__(self) -> str:
        """
        Get the :class:`str` representation of the origin.

        :return: the :class:`str` representation of the origin
        """
        return str(self)

    def __str__(self) -> str:
        """
        Get the :class:`str` representation of the origin.

        :return: the :class:`str` representation of the origin
        """
        detail = f"({self.detail})" if self.detail is not None else ""
        return f"{type(self).__name__.lower()}{detail}"


class Default(Origin):
    """
    Default origin.

    The value is the default value provided by configuration.
    """

    __slots__ = ()

    def __init__(self) -> None:
        """Initialize the origin."""
        Origin.__init__(self, None)


class File(Origin):
    """
    File origin.

    The value comes from a file.
    """

    __slots__ = ()

    def __init__(self, location: "Location") -> None:
        """
        Initialize the origin.

        :param location: The value location in the file
        """
        Origin.__init__(self, location)


class Env(Origin):
    """
    Environment origin.

    The value comes from an environment variable.
    """

    __slots__ = ()

    def __init__(self, varname: str) -> None:
        """
        Initialize the origin.

        :param varname: The name of the environment variable from where the
            value comes
        """
        Origin.__init__(self, varname)


class Cli(Origin):
    """
    Command line interface origin.

    The value comes from the command line interface.
    """

    __slots__ = ()

    def __init__(self) -> None:
        """Initialize the origin."""
        Origin.__init__(self, None)


class ConfigItem:
    """Configuration item."""

    #: Fully qualified name of this item in the configuration
    fqname: str
    #: The value associated with this configuration item
    value: "object | None"
    #: The description of this configuration item
    description: "str | None"
    #: The origin of the value stored in this configuration item
    origin: "Origin | None"
    #: The JSON schema used for the value validation
    schema: "Schema"

    __slots__ = ("fqname", "value", "description", "origin", "schema")

    def __init__(self, fqname: str, schema: "Schema") -> None:
        """
        Initialize the configuration item.

        :param fqname: The fully qualified name of this configuration item with
            respect to the configuration
        :param schema: The JSON schema used to validate a value when it is
            updated
        :raises ~.InvalidSchema: when :arg:`schema` is not valid

        The configuration item is initialized to its vanilla state (i.e. no
        value with no origin).
        """
        self.fqname = fqname
        self.value = None
        self.description = get_description(schema)
        self.origin = None
        result: "Schema | JsonSchemaSchemaError" = copy_and_check_schema(
            schema
        )
        if isinstance(result, JsonSchemaSchemaError):
            raise InvalidSchema(self, result)
        self.schema = result

    def update(self, value: object, origin: Origin) -> None:
        """
        Update this configuration item.

        :param value: The new value
        :param origin: The new origin
        :raises ~.InvalidValue: when :arg:`value` is not valid
        """
        errors: "list[JsonSchemaError] | None" = validate(value, self.schema)
        if errors is not None:
            raise InvalidValue(self, errors)
        self.value = value
        self.origin = origin


class BaseConfig:
    """Base class of all configuration managers."""

    #: The root of the configuration data hierarchy
    __root: "ConfigType"
    #: The schema used for validating the configuration
    __schema: "Schema"

    __slots__ = ("__root", "__schema")

    def __init__(self) -> None:
        """Initialize the configuration manager."""
        self.__root = {}
        self.__schema = new_schema()

    def section_lookup(self, path: str) -> "tuple[ConfigType, Schema, str]":
        """
        Find a section.

        :param path: The key path
        :return: the tuple containing the section where the key should be
            stored, the corresponding schema, and the name of the key
        :raises ~.ConfigError: if the section does not exist or it is not a
            section

        Split :arg:`path` to the section path and key name and then try to find
        the section object corresponding to the section path and the schema
        object describing the section. Both the section object and the schema
        object can be extended about additional items and properties.
        """
        parts = to_parts(path)
        if not parts:
            raise ConfigError("Empty path")
        keyname: str = parts.pop(-1)
        section = self.__root
        schema = self.__schema
        for i, part in enumerate(parts):
            if part not in section:
                raise ConfigError(
                    f"Section `{to_path(parts[:i + 1])}` is not defined"
                )
            section = section[part]
            if not isinstance(section, dict):
                raise ConfigError(
                    f"`{to_path(parts[:i + 1])}` is not a section"
                )
            schema = schema[KW_PROPERTIES][part]
            if KW_REF in schema:
                refname = to_parts(schema[KW_REF])[-1]
                schema = self.__schema[KW_DEFINITIONS][refname]
        return section, schema, keyname

    def define_section(self, path: str, refname: "str | None" = None) -> None:
        """
        Define a new section.

        :param path: The path of a new section
        :param refname: The reference name
        :raises ~.ConfigError: if the section is already defined or some of its
            parents was not defined yet or is not a section

        Note that to define a new section all its parents must be defined. If
        :arg:`refname` is :obj:`None` the section name is used. While defining
        a new section, the corresponding schema is also defined. First, the
        schema that corresponds to the new section's parent is found. Then, the
        reference :arg:`refname` is inserted into the schema under the new
        section's name. Finally, if :arg:`refname` does not have a definition
        yet, it is defined as an empty object.
        """
        section, schema, keyname = self.section_lookup(path)
        if refname is None:
            refname = keyname
        if keyname in section:
            raise ConfigError(f"Section `{path}` is already defined")
        section[keyname] = {}
        schema[KW_PROPERTIES][keyname] = new_ref(refname)
        ensure_ref(self.__schema, refname, new_object())

    @staticmethod
    def make_item_schema(props: "dict[str, object]") -> "Schema":
        """
        Make a schema for configuration item validation.

        :param props: The schema properties
        :return: the schema

        The schema returned is used to validate a value being stored under the
        key. The schema is not checked for validity, this should be done later
        by the consumer. Properties from :arg:`props` are treated in the
        following way:

        * ``key_type`` is the schema type. If it is not provided, the schema
          type is ``string``.
        * ``empty`` indicates that the schema can accept an empty value. In
          case also ``minLength`` is present, it takes priority over ``empty``.
          If missing, ``empty`` is considered :obj:`False`. If ``key_type`` is
          ``enum``, ``empty`` is ignored and discarded from :arg:`props`.
        * Other properties are copied directly to the schema.
        """
        schema_type = props.pop(KW_KEY_TYPE, KW_STRING)
        empty = props.pop(KW_EMPTY, False)
        if schema_type == KW_ENUM:
            schema = {}
        else:
            schema = {KW_TYPE: schema_type}
            # ``minLength`` takes priority over ``empty``:
            if not empty and KW_MINLENGTH not in props:
                props[KW_MINLENGTH] = 1
        schema.update(props)
        return schema

    def define_key(self, path: str, **props: object) -> None:
        """
        Define a key.

        :param path: The path to the key
        :param props: The properties of schema used for key validation
        :raises ~.ConfigError: if the key is already defined or if some of its
            parents is missing or is not a section or the schema build up from
            :arg:`props` is not valid

        To get more information about :arg:`props`, see
        :meth:`~.BaseConfig.make_item_schema` and `JSON Schema Draft 7
        Specifications <https://json-schema.org/specification-links#draft-7>`_.
        """
        section, schema, keyname = self.section_lookup(path)
        if keyname in section:
            raise ConfigError(f"Key `{path}` is already defined")
        item_schema = BaseConfig.make_item_schema(props)
        section[keyname] = ConfigItem(path, item_schema)
        schema[KW_PROPERTIES][keyname] = item_schema

    def item_lookup(self, path: str) -> ConfigItem:
        """
        Find a configuration item.

        :param path: The path to the key under which the configuration item
            lies
        :return: the configuration item
        :raises ~.ConfigError: if the key does not exist or there is no
            configuration item stored under the key
        """
        section, _, keyname = self.section_lookup(path)
        if keyname not in section:
            raise ConfigError(f"Key `{path}` does not exist")
        item = section[keyname]
        if not isinstance(item, ConfigItem):
            raise ConfigError(f"`{path}` is a section")
        return item

    def setval(self, path: str, value: object, origin: Origin) -> None:
        """
        Store the value to the configuration.

        :param path: The path to the key under which the value should be stored
        :param value: The value to be stored
        :param origin: The origin of :arg:`value`
        :raises ~.ConfigError: if the key does not exist or it is a section or
            the value is not valid according to the key schema
        """
        self.item_lookup(path).update(value, origin)

    def getval(self, path: str) -> object:
        """
        Get the value from the configuration.

        :param path: The path to the key under which the value is stored
        :return: the value stored under :arg:`path`
        :raises ~.ConfigError: if the key does not exist or it is a section
        """
        return self.item_lookup(path).value

    def trygetval(self, path: str, default: object = None) -> object:
        """
        Try to get the value from the configuration.

        :param path: The path to the key under which the value is supposed to
            be stored
        :param default: The default value that is returned when there is no
            value stored under :arg:`path` (if not specified, :obj:`None` is
            used)
        :return: the value stored under :arg:`path` or :arg:`default` if such a
            value does not exist
        """
        try:
            value = self.getval(path)
        except ConfigError:
            value = default
        return value


#: The ``color`` key
COLOR_KEY: str = "color"
#: The ``never`` keyword
KW_NEVER: str = "never"
#: The ``always`` keyword
KW_ALWAYS: str = "always"
#: The ``auto`` keyword
KW_AUTO: str = "auto"
#: The template of a color map key. Use :meth:`str.format` with ``name``
#: keyword argument to render it
COLORMAP_KEY: str = "colormap/{name}"
#: The ``vlevel`` key
VLEVEL_KEY: str = "vlevel"
#: The ``dlevel`` key
DLEVEL_KEY: str = "dlevel"
#: The key pointing to the log path
LOG_PATH_KEY: str = "logging/log_path"
#: The key pointing to the log record format
LOG_FORMAT_KEY: str = "logging/record/format"
#: The template of a key pointing to the color of a label of a particular log
#: record. Use :meth:`str.format` with ``level`` keyword argument to render it,
#: where ``level`` is one of ``critical``, ``error``, ``warning``, ``info``, or
#: ``debug``
LOG_LABEL_COLOR_KEY: str = "logging/record/style/{level}/label-color"
#: The template of a key pointing to the color of a message of a particular log
#: record. Use :meth:`str.format` with ``level`` keyword argument to render it,
#: where ``level`` is one of ``critical``, ``error``, ``warning``, ``info``, or
#: ``debug``
LOG_MESSAGE_COLOR_KEY: str = "logging/record/style/{level}/message-color"


class Config(BaseConfig):
    """Default configuration manager."""

    __slots__ = ()

    def __init__(self):
        """Initialize the configuration manager."""
        BaseConfig.__init__(self)
        self.define_key(
            COLOR_KEY,
            key_type="enum",
            enum=[KW_NEWER, KW_ALWAYS, KW_AUTO],
            description=(
                "Output coloring.\n"
                "\n"
                "Decide whether to color the text send to the output:\n"
                "  `never` - never use colors;\n"
                "  `always` - always use colors;\n"
                "  `auto` - decide upon the output device capabilities.\n"
            ),
        )
        self.setval(COLOR_KEY, KW_AUTO, Default())

        self.define_section("colormap")
        self.define_key(
            COLORMAP_KEY.format(name="pass"),
            description=(
                "The color for pass-like messages.\n"
                "\n"
                "Can be used in `color` argument of `ContextProxy.echo`\n"
                "function. See `vutils.cli.base.command.ContextProxy`.\n"
            )
        )
        self.setval(COLORMAP_KEY.format(name="pass"), "bold-green", Default())

        self.define_key(
            COLORMAP_KEY.format(name="fail"),
            description=(
                "The color for fail-like messages.\n"
                "\n"
                "Can be used in `color` argument of `ContextProxy.echo`\n"
                "function. See `vutils.cli.base.command.ContextProxy`.\n"
            )
        )
        self.setval(COLORMAP_KEY.format(name="fail"), "bold-red", Default())

        self.define_key(
            COLORMAP_KEY.format(name="danger"),
            description=(
                "The color for warning-like messages.\n"
                "\n"
                "Can be used in `color` argument of `ContextProxy.echo`\n"
                "function. See `vutils.cli.base.command.ContextProxy`.\n"
            )
        )
        self.setval(
            COLORMAP_KEY.format(name="danger"), "bold-bright-yellow", Default()
        )

        self.define_key(
            COLORMAP_KEY.format(name="info"),
            description=(
                "The color for info-like messages.\n"
                "\n"
                "Can be used in `color` argument of `ContextProxy.echo`\n"
                "function. See `vutils.cli.base.command.ContextProxy`.\n"
            )
        )
        self.setval(COLORMAP_KEY.format(name="info"), "bold-blue", Default())

        self.define_key(
            COLORMAP_KEY.format(name="note"),
            description=(
                "The color for notes.\n"
                "\n"
                "Can be used in `color` argument of `ContextProxy.echo`\n"
                "function. See `vutils.cli.base.command.ContextProxy`.\n"
            )
        )
        self.setval(COLORMAP_KEY.format(name="note"), "yellow", Default())

        self.define_key(
            VLEVEL_KEY,
            key_type="integer",
            minimum=0,
            description=(
                "Verbosity level.\n"
                "\n"
                "Info messages above this level are not logged.\n"
            ),
        )
        self.setval(VLEVEL_KEY, 0, Default())

        self.define_key(
            DLEVEL_KEY,
            key_type="integer",
            minimum=0,
            description=(
                "Debug level.\n"
                "\n"
                "Debug messages above this level are not logged.\n"
            ),
        )
        self.setval(DLEVEL_KEY, 0, Default())

        self.define_section("logging")
        self.define_key(
            LOG_PATH_KEY,
            description=(
                "The path to the application log.\n"
                "\n"
                "Before use, the path is formatted using `str.format()`\n"
                "method with these keyword arguments set:\n"
                "  `progname` - the program name, usually the base name of\n"
                "      `sys.argv[0]`;\n"
                "  `today` - the current date in YYYYMMDD format;\n"
                "  `now` - the current time in HHMMSS format.\n"
                "The path is either absolute or relative to the current\n"
                "working directory. Missing directories are created during\n"
                "first write operation, assuming there are enough\n"
                "permissions.\n"
            ),
        )
        self.setval(
            LOG_PATH_KEY,
            "/var/tmp/{progname}/{progname}_{today}-{now}.log",
            Default(),
        )

        self.define_section("logging/record", "log_record")
        self.define_key(
            LOG_FORMAT_KEY,
            description=(
                "The format of the log record.\n"
                "\n"
                "The format is interpolated using `str.format()` method with\n"
                "these keyword arguments set:\n"
                "  `levelname` - the name of the logging level in upper case\n"
                "      (see the Python `logging` module);\n"
                "  `message` - the message to be logged;\n"
                "  `label_color` - the color of the label, usually ANSI\n"
                "      color code;\n"
                "  `message_color` - the color of the message, usually ANSI\n"
                "      color code;\n"
                "  `color_reset` - restore the default color, usually ANSI\n"
                "      color code.\n"
                "The default format of the log record is `[LABEL]  MESSAGE`\n"
                "where `LABEL` is the upper-cased name of the current\n"
                "logging level.\n"
            ),
        )
        self.setval(
            LOG_FORMAT_KEY,
            (
                "{label_color}[{levelname}]{color_reset}"
                "  "
                "{message_color}{message}{color_reset}"
            ),
            Default(),
        )

        self.define_section("logging/record/style", "log_record_style")
        self.define_section(
            "logging/record/style/critical", "log_record_style_item"
        )
        self.define_key(
            LOG_LABEL_COLOR_KEY.format(level="critical"),
            description=(
                "The label color.\n"
                "\n"
                "See `vutils.cli.base.io.ColorFactory`.\n"
            ),
        )
        self.define_key(
            LOG_MESSAGE_COLOR_KEY.format(level="critical"),
            description=(
                "The message color.\n"
                "\n"
                "See `vutils.cli.base.io.ColorFactory`.\n"
            ),
        )
        self.setval(
            LOG_LABEL_COLOR_KEY.format(level="critical"), "bold-red", Default()
        )
        self.setval(
            LOG_MESSAGE_COLOR_KEY.format(level="critical"),
            "bold-red",
            Default(),
        )

        self.define_section(
            "logging/record/style/error", "log_record_style_item"
        )
        self.setval(
            LOG_LABEL_COLOR_KEY.format(level="error"), "bold-red", Default()
        )
        self.setval(
            LOG_MESSAGE_COLOR_KEY.format(level="error"), "red", Default()
        )

        self.define_section(
            "logging/record/style/warning", "log_record_style_item"
        )
        self.setval(
            LOG_LABEL_COLOR_KEY.format(level="warning"),
            "bold-bright-yellow",
            Default(),
        )
        self.setval(
            LOG_MESSAGE_COLOR_KEY.format(level="warning"),
            "bright-yellow",
            Default(),
        )

        self.define_section(
            "logging/record/style/info", "log_record_style_item"
        )
        self.setval(
            LOG_LABEL_COLOR_KEY.format(level="info"),
            "bold-bright-blue",
            Default(),
        )
        self.setval(
            LOG_MESSAGE_COLOR_KEY.format(level="info"),
            "bright-blue",
            Default(),
        )

        self.define_section(
            "logging/record/style/debug", "log_record_style_item"
        )
        self.setval(
            LOG_LABEL_COLOR_KEY.format(level="debug"), "bold-yellow", Default()
        )
        self.setval(
            LOG_MESSAGE_COLOR_KEY.format(level="debug"), "yellow", Default()
        )
