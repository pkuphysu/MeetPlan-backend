
def user_create_callback(sender, **kwargs):
    user = kwargs['user']
    user.add_obj_perm('change_user', user)
