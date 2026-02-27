from .mb_color_harmony_wheel import MBColorHarmonyWheelDocker
from krita import DockWidgetFactory, DockWidgetFactoryBase, Krita


instance = Krita.instance()
dock_widget_factory = DockWidgetFactory(
    "mb_color_harmony_wheel",
    DockWidgetFactoryBase.DockRight,
    MBColorHarmonyWheelDocker,
)
instance.addDockWidgetFactory(dock_widget_factory)