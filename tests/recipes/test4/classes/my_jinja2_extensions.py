def filter_neighbor_applications_as_tuple(application):
    return [(app.type.lower(), app.name.lower(), app.__class__.__name__.lower()) for app in application.host.applications]

