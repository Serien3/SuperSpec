from superspec.actions.openspec_actions import (
    handle_openspec_apply,
    handle_openspec_design,
    handle_openspec_proposal,
    handle_openspec_specs,
    handle_openspec_tasks,
)

action_handlers = {
    "openspec.proposal": handle_openspec_proposal,
    "openspec.specs": handle_openspec_specs,
    "openspec.design": handle_openspec_design,
    "openspec.tasks": handle_openspec_tasks,
    "openspec.apply": handle_openspec_apply,
}


def get_action_handler(action_type: str):
    return action_handlers.get(action_type)
