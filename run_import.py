import traceback
try:
    import old_app
except Exception:
    traceback.print_exc()
    raise
print('imported old_app successfully')
