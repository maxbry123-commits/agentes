# WORKFLOW STATUS · 100% lista W01–W17

Control layer Wordflow **cerrada** en contratos + wiring.

Entry: `wordflow.control_bus.ControlBus`

```python
from wordflow.control_bus import ControlBus
bus = ControlBus("./state")
bus.start_mission(workflow_id="w1", goals_in={...}, estimated_tokens=1000)
bus.finish_mission(workflow_id="w1", goals_out={...}, result="...")
```
