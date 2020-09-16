import eventlet

patched = False

default_eventlet_monkey_patch = eventlet.monkey_patch


def eventlet_monkey_patch(**on):
    force = on.pop('force', False)
    global patched

    if not force and patched:
        return

    default_eventlet_monkey_patch(**on)
    patched = True


def monkey_patch():
    """打补丁

    """
    eventlet.monkey_patch = eventlet_monkey_patch
