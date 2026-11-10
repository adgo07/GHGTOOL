"""Local painting for existing accounting spin-box buttons; native events stay."""
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor,QPainter,QPen,QPolygonF
from PySide6.QtWidgets import QAbstractSpinBox,QSpinBox,QStyle,QStyleOptionSpinBox
from .design_tokens import PRIMARY_TEXT,DISABLED_TEXT,SURFACE_MUTED


class AccountingSpinBox(QSpinBox):
    def paintEvent(self,event):
        super().paintEvent(event)
        option=QStyleOptionSpinBox();self.initStyleOption(option)
        painter=QPainter(self);painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for control,flag,up in (
            (QStyle.SubControl.SC_SpinBoxUp,QAbstractSpinBox.StepEnabledFlag.StepUpEnabled,True),
            (QStyle.SubControl.SC_SpinBoxDown,QAbstractSpinBox.StepEnabledFlag.StepDownEnabled,False),
        ):
            box=self.style().subControlRect(QStyle.ComplexControl.CC_SpinBox,option,control,self)
            if box.isEmpty():continue
            painter.fillRect(box.adjusted(1,1,-1,-1),QColor(SURFACE_MUTED))
            painter.setPen(QPen(QColor(PRIMARY_TEXT if self.isEnabled() and option.stepEnabled & flag else DISABLED_TEXT),1.6))
            x,y=box.center().x(),box.center().y();direction=-1 if up else 1
            painter.drawPolyline(QPolygonF([QPointF(x-3,y-direction),QPointF(x,y+direction*2),QPointF(x+3,y-direction)]))
        painter.end()
