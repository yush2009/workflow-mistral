#/usr/bin/python
# -*- coding: utf_8 -*-

from mistral.workflow import states

# task start event
TASK_START="task_start"
# task runnint event
TASK_RUNNING = "task_running"
# task end event
TASK_END = "task_end"
# task pause event
TASK_PAUSE = "task_pause"
# task resume event
TASK_RESUME = "task_resume"
# task redo event
TASK_REDO = "task_redo"
# task pass event
TASK_PASS = "task_pass"

# task running event
TASK_ACTION = "task_action"

# workflow execution start event
EXECUTION_START = "execution_start"
# workflow execution end event
EXECUTION_END = "execution_end"
# workflow execution pause event
EXECUTION_PAUSE = "execution_pause"
# workflow execution resume event
EXECUTION_RESUME = "execution_resume"

# workflow execution rollback start event
EXECUTION_ROLLBACK_START = "execution_rollback_start"
# workflow execution rollback end event
EXECUTION_ROLLBACK_END = "execution_rollback_end"

TASK_ROLLBACK = "task_rollback"


class EventCategory():
    """Kafka事件分类 Workflow 或者 Task"""

    WORKFLOW = 'W'
    TASK = 'T'

    def is_workflow(self, category):
        if category == self.WORKFLOW:
            return True
        return False

    def is_task(self, category):
        if category == self.TASK:
            return True
        return False

def wf_parse(cur_state, state):
    return parse(cur_state, state, EventCategory.WORKFLOW)

def tk_parse(cur_state, state):
    return parse(cur_state, state, EventCategory.TASK)

def parse(cur_state, state, category=EventCategory.WORKFLOW):
    """
    states {
        IDLE = 'IDLE'
        WAITING = 'WAITING'
        RUNNING = 'RUNNING'
        RUNNING_DELAYED = 'DELAYED'
        PAUSED = 'PAUSED'
        SUCCESS = 'SUCCESS'
        CANCELLED = 'CANCELLED'
        ERROR = 'ERROR'
    }
    :param wtype: Workflow or Task
    :param cur_state: 当前状态
    :param state: 要更新到的状态
    :return: etype
    """
    if cur_state == states.IDLE and state == states.RUNNING:
        if EventCategory().is_task(category):
            return TASK_START
        else:
            return EXECUTION_START
    elif cur_state == states.WAITING and state == states.RUNNING:
        if EventCategory().is_task(category):
            return TASK_RUNNING
    elif states.is_completed(state):
        if EventCategory().is_task(category):
            return TASK_END
        else:
            return EXECUTION_END
    elif states.is_paused(state):
        if EventCategory().is_task(category):
            return TASK_PAUSE
        else:
            return EXECUTION_PAUSE
    elif cur_state == states.PAUSED and state == states.RUNNING:
        if EventCategory().is_task(category):
            return TASK_RESUME
        else:
            return EXECUTION_RESUME
