from __future__ import annotations
import falcor.falcor_ext.ui
import typing
import falcor.falcor_ext

__all__ = [
    "Button",
    "Checkbox",
    "Combobox",
    "DragFloat",
    "DragFloat2",
    "DragFloat3",
    "DragFloat4",
    "DragInt",
    "DragInt2",
    "DragInt3",
    "DragInt4",
    "Group",
    "ProgressBar",
    "Property",
    "Screen",
    "SliderFlags",
    "SliderFloat",
    "SliderFloat2",
    "SliderFloat3",
    "SliderFloat4",
    "SliderInt",
    "SliderInt2",
    "SliderInt3",
    "SliderInt4",
    "Text",
    "Widget",
    "WidgetVector",
    "Window"
]


class Widget():
    @property
    def children(self) -> WidgetVector:
        """
        :type: WidgetVector
        """
    @property
    def enabled(self) -> bool:
        """
        :type: bool
        """
    @enabled.setter
    def enabled(self, arg1: bool) -> None:
        pass
    @property
    def parent(self) -> Widget:
        """
        :type: Widget
        """
    @parent.setter
    def parent(self, arg1: Widget) -> None:
        pass
    @property
    def visible(self) -> bool:
        """
        :type: bool
        """
    @visible.setter
    def visible(self, arg1: bool) -> None:
        pass
    pass
class Property(Widget):
    @property
    def change_callback(self) -> typing.Callable[[], None]:
        """
        :type: typing.Callable[[], None]
        """
    @change_callback.setter
    def change_callback(self, arg1: typing.Callable[[], None]) -> None:
        pass
    @property
    def label(self) -> str:
        """
        :type: str
        """
    @label.setter
    def label(self, arg1: str) -> None:
        pass
    pass
class Combobox(Property, Widget):
    def __init__(self, parent: Widget, label: str = '', change_callback: typing.Callable[[], None] = None, items: typing.List[str] = [], value: int = 0) -> None: ...
    @property
    def items(self) -> typing.List[str]:
        """
        :type: typing.List[str]
        """
    @items.setter
    def items(self, arg1: typing.List[str]) -> None:
        pass
    @property
    def value(self) -> int:
        """
        :type: int
        """
    @value.setter
    def value(self, arg1: int) -> None:
        pass
    pass
class DragFloat(Property, Widget):
    def __init__(self, parent: Widget, label: str = '', change_callback: typing.Callable[[], None] = None, value: float = 0.0, speed: float = 1.0, min: float = 0.0, max: float = 0.0, format: str = '%.3f', flags: SliderFlags = SliderFlags.None_) -> None: ...
    @property
    def flags(self) -> SliderFlags:
        """
        :type: SliderFlags
        """
    @flags.setter
    def flags(self, arg1: SliderFlags) -> None:
        pass
    @property
    def format(self) -> str:
        """
        :type: str
        """
    @format.setter
    def format(self, arg1: str) -> None:
        pass
    @property
    def max(self) -> float:
        """
        :type: float
        """
    @max.setter
    def max(self, arg1: float) -> None:
        pass
    @property
    def min(self) -> float:
        """
        :type: float
        """
    @min.setter
    def min(self, arg1: float) -> None:
        pass
    @property
    def speed(self) -> float:
        """
        :type: float
        """
    @speed.setter
    def speed(self, arg1: float) -> None:
        pass
    @property
    def value(self) -> float:
        """
        :type: float
        """
    @value.setter
    def value(self, arg1: float) -> None:
        pass
    pass
class DragFloat2(Property, Widget):
    def __init__(self, parent: Widget, label: str = '', change_callback: typing.Callable[[], None] = None, value: falcor.falcor_ext.float2 = float2(0.000000, 0.000000), speed: float = 1.0, min: float = 0.0, max: float = 0.0, format: str = '%.3f', flags: SliderFlags = SliderFlags.None_) -> None: ...
    @property
    def flags(self) -> SliderFlags:
        """
        :type: SliderFlags
        """
    @flags.setter
    def flags(self, arg1: SliderFlags) -> None:
        pass
    @property
    def format(self) -> str:
        """
        :type: str
        """
    @format.setter
    def format(self, arg1: str) -> None:
        pass
    @property
    def max(self) -> float:
        """
        :type: float
        """
    @max.setter
    def max(self, arg1: float) -> None:
        pass
    @property
    def min(self) -> float:
        """
        :type: float
        """
    @min.setter
    def min(self, arg1: float) -> None:
        pass
    @property
    def speed(self) -> float:
        """
        :type: float
        """
    @speed.setter
    def speed(self, arg1: float) -> None:
        pass
    @property
    def value(self) -> falcor.falcor_ext.float2:
        """
        :type: falcor.falcor_ext.float2
        """
    @value.setter
    def value(self, arg1: falcor.falcor_ext.float2) -> None:
        pass
    pass
class DragFloat3(Property, Widget):
    def __init__(self, parent: Widget, label: str = '', change_callback: typing.Callable[[], None] = None, value: falcor.falcor_ext.float3 = float3(0.000000, 0.000000, 0.000000), speed: float = 1.0, min: float = 0.0, max: float = 0.0, format: str = '%.3f', flags: SliderFlags = SliderFlags.None_) -> None: ...
    @property
    def flags(self) -> SliderFlags:
        """
        :type: SliderFlags
        """
    @flags.setter
    def flags(self, arg1: SliderFlags) -> None:
        pass
    @property
    def format(self) -> str:
        """
        :type: str
        """
    @format.setter
    def format(self, arg1: str) -> None:
        pass
    @property
    def max(self) -> float:
        """
        :type: float
        """
    @max.setter
    def max(self, arg1: float) -> None:
        pass
    @property
    def min(self) -> float:
        """
        :type: float
        """
    @min.setter
    def min(self, arg1: float) -> None:
        pass
    @property
    def speed(self) -> float:
        """
        :type: float
        """
    @speed.setter
    def speed(self, arg1: float) -> None:
        pass
    @property
    def value(self) -> falcor.falcor_ext.float3:
        """
        :type: falcor.falcor_ext.float3
        """
    @value.setter
    def value(self, arg1: falcor.falcor_ext.float3) -> None:
        pass
    pass
class DragFloat4(Property, Widget):
    def __init__(self, parent: Widget, label: str = '', change_callback: typing.Callable[[], None] = None, value: falcor.falcor_ext.float4 = float4(0.000000, 0.000000, 0.000000, 0.000000), speed: float = 1.0, min: float = 0.0, max: float = 0.0, format: str = '%.3f', flags: SliderFlags = SliderFlags.None_) -> None: ...
    @property
    def flags(self) -> SliderFlags:
        """
        :type: SliderFlags
        """
    @flags.setter
    def flags(self, arg1: SliderFlags) -> None:
        pass
    @property
    def format(self) -> str:
        """
        :type: str
        """
    @format.setter
    def format(self, arg1: str) -> None:
        pass
    @property
    def max(self) -> float:
        """
        :type: float
        """
    @max.setter
    def max(self, arg1: float) -> None:
        pass
    @property
    def min(self) -> float:
        """
        :type: float
        """
    @min.setter
    def min(self, arg1: float) -> None:
        pass
    @property
    def speed(self) -> float:
        """
        :type: float
        """
    @speed.setter
    def speed(self, arg1: float) -> None:
        pass
    @property
    def value(self) -> falcor.falcor_ext.float4:
        """
        :type: falcor.falcor_ext.float4
        """
    @value.setter
    def value(self, arg1: falcor.falcor_ext.float4) -> None:
        pass
    pass
class DragInt(Property, Widget):
    def __init__(self, parent: Widget, label: str = '', change_callback: typing.Callable[[], None] = None, value: int = 0, speed: float = 1.0, min: int = 0, max: int = 0, format: str = '%d', flags: SliderFlags = SliderFlags.None_) -> None: ...
    @property
    def flags(self) -> SliderFlags:
        """
        :type: SliderFlags
        """
    @flags.setter
    def flags(self, arg1: SliderFlags) -> None:
        pass
    @property
    def format(self) -> str:
        """
        :type: str
        """
    @format.setter
    def format(self, arg1: str) -> None:
        pass
    @property
    def max(self) -> int:
        """
        :type: int
        """
    @max.setter
    def max(self, arg1: int) -> None:
        pass
    @property
    def min(self) -> int:
        """
        :type: int
        """
    @min.setter
    def min(self, arg1: int) -> None:
        pass
    @property
    def speed(self) -> int:
        """
        :type: int
        """
    @speed.setter
    def speed(self, arg1: int) -> None:
        pass
    @property
    def value(self) -> int:
        """
        :type: int
        """
    @value.setter
    def value(self, arg1: int) -> None:
        pass
    pass
class DragInt2(Property, Widget):
    def __init__(self, parent: Widget, label: str = '', change_callback: typing.Callable[[], None] = None, value: falcor.falcor_ext.int2 = int2(0, 0), speed: float = 1.0, min: int = 0, max: int = 0, format: str = '%d', flags: SliderFlags = SliderFlags.None_) -> None: ...
    @property
    def flags(self) -> SliderFlags:
        """
        :type: SliderFlags
        """
    @flags.setter
    def flags(self, arg1: SliderFlags) -> None:
        pass
    @property
    def format(self) -> str:
        """
        :type: str
        """
    @format.setter
    def format(self, arg1: str) -> None:
        pass
    @property
    def max(self) -> int:
        """
        :type: int
        """
    @max.setter
    def max(self, arg1: int) -> None:
        pass
    @property
    def min(self) -> int:
        """
        :type: int
        """
    @min.setter
    def min(self, arg1: int) -> None:
        pass
    @property
    def speed(self) -> int:
        """
        :type: int
        """
    @speed.setter
    def speed(self, arg1: int) -> None:
        pass
    @property
    def value(self) -> falcor.falcor_ext.int2:
        """
        :type: falcor.falcor_ext.int2
        """
    @value.setter
    def value(self, arg1: falcor.falcor_ext.int2) -> None:
        pass
    pass
class DragInt3(Property, Widget):
    def __init__(self, parent: Widget, label: str = '', change_callback: typing.Callable[[], None] = None, value: falcor.falcor_ext.int3 = int3(0, 0, 0), speed: float = 1.0, min: int = 0, max: int = 0, format: str = '%d', flags: SliderFlags = SliderFlags.None_) -> None: ...
    @property
    def flags(self) -> SliderFlags:
        """
        :type: SliderFlags
        """
    @flags.setter
    def flags(self, arg1: SliderFlags) -> None:
        pass
    @property
    def format(self) -> str:
        """
        :type: str
        """
    @format.setter
    def format(self, arg1: str) -> None:
        pass
    @property
    def max(self) -> int:
        """
        :type: int
        """
    @max.setter
    def max(self, arg1: int) -> None:
        pass
    @property
    def min(self) -> int:
        """
        :type: int
        """
    @min.setter
    def min(self, arg1: int) -> None:
        pass
    @property
    def speed(self) -> int:
        """
        :type: int
        """
    @speed.setter
    def speed(self, arg1: int) -> None:
        pass
    @property
    def value(self) -> falcor.falcor_ext.int3:
        """
        :type: falcor.falcor_ext.int3
        """
    @value.setter
    def value(self, arg1: falcor.falcor_ext.int3) -> None:
        pass
    pass
class DragInt4(Property, Widget):
    def __init__(self, parent: Widget, label: str = '', change_callback: typing.Callable[[], None] = None, value: falcor.falcor_ext.int4 = int4(0, 0, 0, 0), speed: float = 1.0, min: int = 0, max: int = 0, format: str = '%d', flags: SliderFlags = SliderFlags.None_) -> None: ...
    @property
    def flags(self) -> SliderFlags:
        """
        :type: SliderFlags
        """
    @flags.setter
    def flags(self, arg1: SliderFlags) -> None:
        pass
    @property
    def format(self) -> str:
        """
        :type: str
        """
    @format.setter
    def format(self, arg1: str) -> None:
        pass
    @property
    def max(self) -> int:
        """
        :type: int
        """
    @max.setter
    def max(self, arg1: int) -> None:
        pass
    @property
    def min(self) -> int:
        """
        :type: int
        """
    @min.setter
    def min(self, arg1: int) -> None:
        pass
    @property
    def speed(self) -> int:
        """
        :type: int
        """
    @speed.setter
    def speed(self, arg1: int) -> None:
        pass
    @property
    def value(self) -> falcor.falcor_ext.int4:
        """
        :type: falcor.falcor_ext.int4
        """
    @value.setter
    def value(self, arg1: falcor.falcor_ext.int4) -> None:
        pass
    pass
class Group(Widget):
    def __init__(self, parent: Widget, label: str = '') -> None: ...
    @property
    def label(self) -> str:
        """
        :type: str
        """
    @label.setter
    def label(self, arg1: str) -> None:
        pass
    pass
class ProgressBar(Widget):
    def __init__(self, parent: Widget, fraction: float = 0.0) -> None: ...
    @property
    def fraction(self) -> float:
        """
        :type: float
        """
    @fraction.setter
    def fraction(self, arg1: float) -> None:
        pass
    pass
class Checkbox(Property, Widget):
    def __init__(self, parent: Widget, label: str = '', change_callback: typing.Callable[[], None] = None, value: bool = False) -> None: ...
    @property
    def value(self) -> bool:
        """
        :type: bool
        """
    @value.setter
    def value(self, arg1: bool) -> None:
        pass
    pass
class Screen(Widget):
    pass
class SliderFlags():
    """
    Members:

      None_

      AlwaysClamp

      Logarithmic

      NoRoundToFormat

      NoInput
    """
    def __eq__(self, other: object) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: object) -> bool: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: int) -> None: ...
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @property
    def value(self) -> int:
        """
        :type: int
        """
    AlwaysClamp: falcor.falcor_ext.ui.SliderFlags # value = SliderFlags.AlwaysClamp
    Logarithmic: falcor.falcor_ext.ui.SliderFlags # value = SliderFlags.Logarithmic
    NoInput: falcor.falcor_ext.ui.SliderFlags # value = SliderFlags.NoInput
    NoRoundToFormat: falcor.falcor_ext.ui.SliderFlags # value = SliderFlags.NoRoundToFormat
    None_: falcor.falcor_ext.ui.SliderFlags # value = SliderFlags.None_
    __members__: dict # value = {'None_': SliderFlags.None_, 'AlwaysClamp': SliderFlags.AlwaysClamp, 'Logarithmic': SliderFlags.Logarithmic, 'NoRoundToFormat': SliderFlags.NoRoundToFormat, 'NoInput': SliderFlags.NoInput}
    pass
class SliderFloat(Property, Widget):
    def __init__(self, parent: Widget, label: str = '', change_callback: typing.Callable[[], None] = None, value: float = 0.0, min: float = 0.0, max: float = 0.0, format: str = '%.3f', flags: SliderFlags = SliderFlags.None_) -> None: ...
    @property
    def flags(self) -> SliderFlags:
        """
        :type: SliderFlags
        """
    @flags.setter
    def flags(self, arg1: SliderFlags) -> None:
        pass
    @property
    def format(self) -> str:
        """
        :type: str
        """
    @format.setter
    def format(self, arg1: str) -> None:
        pass
    @property
    def max(self) -> float:
        """
        :type: float
        """
    @max.setter
    def max(self, arg1: float) -> None:
        pass
    @property
    def min(self) -> float:
        """
        :type: float
        """
    @min.setter
    def min(self, arg1: float) -> None:
        pass
    @property
    def value(self) -> float:
        """
        :type: float
        """
    @value.setter
    def value(self, arg1: float) -> None:
        pass
    pass
class SliderFloat2(Property, Widget):
    def __init__(self, parent: Widget, label: str = '', change_callback: typing.Callable[[], None] = None, value: falcor.falcor_ext.float2 = float2(0.000000, 0.000000), min: float = 0.0, max: float = 0.0, format: str = '%.3f', flags: SliderFlags = SliderFlags.None_) -> None: ...
    @property
    def flags(self) -> SliderFlags:
        """
        :type: SliderFlags
        """
    @flags.setter
    def flags(self, arg1: SliderFlags) -> None:
        pass
    @property
    def format(self) -> str:
        """
        :type: str
        """
    @format.setter
    def format(self, arg1: str) -> None:
        pass
    @property
    def max(self) -> float:
        """
        :type: float
        """
    @max.setter
    def max(self, arg1: float) -> None:
        pass
    @property
    def min(self) -> float:
        """
        :type: float
        """
    @min.setter
    def min(self, arg1: float) -> None:
        pass
    @property
    def value(self) -> falcor.falcor_ext.float2:
        """
        :type: falcor.falcor_ext.float2
        """
    @value.setter
    def value(self, arg1: falcor.falcor_ext.float2) -> None:
        pass
    pass
class SliderFloat3(Property, Widget):
    def __init__(self, parent: Widget, label: str = '', change_callback: typing.Callable[[], None] = None, value: falcor.falcor_ext.float3 = float3(0.000000, 0.000000, 0.000000), min: float = 0.0, max: float = 0.0, format: str = '%.3f', flags: SliderFlags = SliderFlags.None_) -> None: ...
    @property
    def flags(self) -> SliderFlags:
        """
        :type: SliderFlags
        """
    @flags.setter
    def flags(self, arg1: SliderFlags) -> None:
        pass
    @property
    def format(self) -> str:
        """
        :type: str
        """
    @format.setter
    def format(self, arg1: str) -> None:
        pass
    @property
    def max(self) -> float:
        """
        :type: float
        """
    @max.setter
    def max(self, arg1: float) -> None:
        pass
    @property
    def min(self) -> float:
        """
        :type: float
        """
    @min.setter
    def min(self, arg1: float) -> None:
        pass
    @property
    def value(self) -> falcor.falcor_ext.float3:
        """
        :type: falcor.falcor_ext.float3
        """
    @value.setter
    def value(self, arg1: falcor.falcor_ext.float3) -> None:
        pass
    pass
class SliderFloat4(Property, Widget):
    def __init__(self, parent: Widget, label: str = '', change_callback: typing.Callable[[], None] = None, value: falcor.falcor_ext.float4 = float4(0.000000, 0.000000, 0.000000, 0.000000), min: float = 0.0, max: float = 0.0, format: str = '%.3f', flags: SliderFlags = SliderFlags.None_) -> None: ...
    @property
    def flags(self) -> SliderFlags:
        """
        :type: SliderFlags
        """
    @flags.setter
    def flags(self, arg1: SliderFlags) -> None:
        pass
    @property
    def format(self) -> str:
        """
        :type: str
        """
    @format.setter
    def format(self, arg1: str) -> None:
        pass
    @property
    def max(self) -> float:
        """
        :type: float
        """
    @max.setter
    def max(self, arg1: float) -> None:
        pass
    @property
    def min(self) -> float:
        """
        :type: float
        """
    @min.setter
    def min(self, arg1: float) -> None:
        pass
    @property
    def value(self) -> falcor.falcor_ext.float4:
        """
        :type: falcor.falcor_ext.float4
        """
    @value.setter
    def value(self, arg1: falcor.falcor_ext.float4) -> None:
        pass
    pass
class SliderInt(Property, Widget):
    def __init__(self, parent: Widget, label: str = '', change_callback: typing.Callable[[], None] = None, value: int = 0, min: int = 0, max: int = 0, format: str = '%d', flags: SliderFlags = SliderFlags.None_) -> None: ...
    @property
    def flags(self) -> SliderFlags:
        """
        :type: SliderFlags
        """
    @flags.setter
    def flags(self, arg1: SliderFlags) -> None:
        pass
    @property
    def format(self) -> str:
        """
        :type: str
        """
    @format.setter
    def format(self, arg1: str) -> None:
        pass
    @property
    def max(self) -> int:
        """
        :type: int
        """
    @max.setter
    def max(self, arg1: int) -> None:
        pass
    @property
    def min(self) -> int:
        """
        :type: int
        """
    @min.setter
    def min(self, arg1: int) -> None:
        pass
    @property
    def value(self) -> int:
        """
        :type: int
        """
    @value.setter
    def value(self, arg1: int) -> None:
        pass
    pass
class SliderInt2(Property, Widget):
    def __init__(self, parent: Widget, label: str = '', change_callback: typing.Callable[[], None] = None, value: falcor.falcor_ext.int2 = int2(0, 0), min: int = 0, max: int = 0, format: str = '%d', flags: SliderFlags = SliderFlags.None_) -> None: ...
    @property
    def flags(self) -> SliderFlags:
        """
        :type: SliderFlags
        """
    @flags.setter
    def flags(self, arg1: SliderFlags) -> None:
        pass
    @property
    def format(self) -> str:
        """
        :type: str
        """
    @format.setter
    def format(self, arg1: str) -> None:
        pass
    @property
    def max(self) -> int:
        """
        :type: int
        """
    @max.setter
    def max(self, arg1: int) -> None:
        pass
    @property
    def min(self) -> int:
        """
        :type: int
        """
    @min.setter
    def min(self, arg1: int) -> None:
        pass
    @property
    def value(self) -> falcor.falcor_ext.int2:
        """
        :type: falcor.falcor_ext.int2
        """
    @value.setter
    def value(self, arg1: falcor.falcor_ext.int2) -> None:
        pass
    pass
class SliderInt3(Property, Widget):
    def __init__(self, parent: Widget, label: str = '', change_callback: typing.Callable[[], None] = None, value: falcor.falcor_ext.int3 = int3(0, 0, 0), min: int = 0, max: int = 0, format: str = '%d', flags: SliderFlags = SliderFlags.None_) -> None: ...
    @property
    def flags(self) -> SliderFlags:
        """
        :type: SliderFlags
        """
    @flags.setter
    def flags(self, arg1: SliderFlags) -> None:
        pass
    @property
    def format(self) -> str:
        """
        :type: str
        """
    @format.setter
    def format(self, arg1: str) -> None:
        pass
    @property
    def max(self) -> int:
        """
        :type: int
        """
    @max.setter
    def max(self, arg1: int) -> None:
        pass
    @property
    def min(self) -> int:
        """
        :type: int
        """
    @min.setter
    def min(self, arg1: int) -> None:
        pass
    @property
    def value(self) -> falcor.falcor_ext.int3:
        """
        :type: falcor.falcor_ext.int3
        """
    @value.setter
    def value(self, arg1: falcor.falcor_ext.int3) -> None:
        pass
    pass
class SliderInt4(Property, Widget):
    def __init__(self, parent: Widget, label: str = '', change_callback: typing.Callable[[], None] = None, value: falcor.falcor_ext.int4 = int4(0, 0, 0, 0), min: int = 0, max: int = 0, format: str = '%d', flags: SliderFlags = SliderFlags.None_) -> None: ...
    @property
    def flags(self) -> SliderFlags:
        """
        :type: SliderFlags
        """
    @flags.setter
    def flags(self, arg1: SliderFlags) -> None:
        pass
    @property
    def format(self) -> str:
        """
        :type: str
        """
    @format.setter
    def format(self, arg1: str) -> None:
        pass
    @property
    def max(self) -> int:
        """
        :type: int
        """
    @max.setter
    def max(self, arg1: int) -> None:
        pass
    @property
    def min(self) -> int:
        """
        :type: int
        """
    @min.setter
    def min(self, arg1: int) -> None:
        pass
    @property
    def value(self) -> falcor.falcor_ext.int4:
        """
        :type: falcor.falcor_ext.int4
        """
    @value.setter
    def value(self, arg1: falcor.falcor_ext.int4) -> None:
        pass
    pass
class Text(Widget):
    def __init__(self, parent: Widget, text: str = '') -> None: ...
    @property
    def text(self) -> str:
        """
        :type: str
        """
    @text.setter
    def text(self, arg1: str) -> None:
        pass
    pass
class Button(Widget):
    def __init__(self, parent: Widget, label: str = '', callback: typing.Callable[[], None] = None) -> None: ...
    @property
    def callback(self) -> typing.Callable[[], None]:
        """
        :type: typing.Callable[[], None]
        """
    @callback.setter
    def callback(self, arg1: typing.Callable[[], None]) -> None:
        pass
    @property
    def label(self) -> str:
        """
        :type: str
        """
    @label.setter
    def label(self, arg1: str) -> None:
        pass
    pass
class WidgetVector():
    def __bool__(self) -> bool: 
        """
        Check whether the list is nonempty
        """
    def __contains__(self, x: Widget) -> bool: 
        """
        Return true the container contains ``x``
        """
    @typing.overload
    def __delitem__(self, arg0: int) -> None: 
        """
        Delete the list elements at index ``i``

        Delete list elements using a slice object
        """
    @typing.overload
    def __delitem__(self, arg0: slice) -> None: ...
    def __eq__(self, arg0: WidgetVector) -> bool: ...
    @typing.overload
    def __getitem__(self, arg0: int) -> Widget: 
        """
        Retrieve list elements using a slice object
        """
    @typing.overload
    def __getitem__(self, s: slice) -> WidgetVector: ...
    @typing.overload
    def __init__(self) -> None: 
        """
        Copy constructor
        """
    @typing.overload
    def __init__(self, arg0: WidgetVector) -> None: ...
    @typing.overload
    def __init__(self, arg0: typing.Iterable) -> None: ...
    def __iter__(self) -> typing.Iterator: ...
    def __len__(self) -> int: ...
    def __ne__(self, arg0: WidgetVector) -> bool: ...
    def __repr__(self) -> str: 
        """
        Return the canonical string representation of this list.
        """
    @typing.overload
    def __setitem__(self, arg0: int, arg1: Widget) -> None: 
        """
        Assign list elements using a slice object
        """
    @typing.overload
    def __setitem__(self, arg0: slice, arg1: WidgetVector) -> None: ...
    def append(self, x: Widget) -> None: 
        """
        Add an item to the end of the list
        """
    def clear(self) -> None: 
        """
        Clear the contents
        """
    def count(self, x: Widget) -> int: 
        """
        Return the number of times ``x`` appears in the list
        """
    @typing.overload
    def extend(self, L: WidgetVector) -> None: 
        """
        Extend the list by appending all the items in the given list

        Extend the list by appending all the items in the given list
        """
    @typing.overload
    def extend(self, L: typing.Iterable) -> None: ...
    def insert(self, i: int, x: Widget) -> None: 
        """
        Insert an item at a given position.
        """
    @typing.overload
    def pop(self) -> Widget: 
        """
        Remove and return the last item

        Remove and return the item at index ``i``
        """
    @typing.overload
    def pop(self, i: int) -> Widget: ...
    def remove(self, x: Widget) -> None: 
        """
        Remove the first item from the list whose value is x. It is an error if there is no such item.
        """
    __hash__ = None
    pass
class Window(Widget):
    def __init__(self, parent: Widget, title: str = '', position: falcor.falcor_ext.float2 = float2(10.000000, 10.000000), size: falcor.falcor_ext.float2 = float2(400.000000, 400.000000)) -> None: ...
    def close(self) -> None: ...
    def show(self) -> None: ...
    @property
    def position(self) -> falcor.falcor_ext.float2:
        """
        :type: falcor.falcor_ext.float2
        """
    @position.setter
    def position(self, arg1: falcor.falcor_ext.float2) -> None:
        pass
    @property
    def size(self) -> falcor.falcor_ext.float2:
        """
        :type: falcor.falcor_ext.float2
        """
    @size.setter
    def size(self, arg1: falcor.falcor_ext.float2) -> None:
        pass
    @property
    def title(self) -> str:
        """
        :type: str
        """
    @title.setter
    def title(self, arg1: str) -> None:
        pass
    pass
