from django.shortcuts import redirect

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login/admin/")
        if request.user.role != "ADMIN":
            return redirect("/")
        return view_func(request, *args, **kwargs)
    return wrapper