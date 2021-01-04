class MunieventsError(Exception):
    pass

class NotFoundError(MunieventsError):
    pass

class TooManyResultsError(MunieventsError):
    pass