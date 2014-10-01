from functools import wraps

# request = 'any' || 'initial' || 'session'

def lti(*args,**kwargs):
    def _lti(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            print "request kind {} ".format(request)
            ret = f(*args,**kwargs)
            return ret
        return wrapper
    if len(args) == 1 and callable(args[0]):
        # No arguments, this is the decorator
        # Set default values for the arguments
        enter_string = 'entering'
        exit_string = 'exiting'
        return _lti(args[0])
    else:
        request = args
        return _lti
