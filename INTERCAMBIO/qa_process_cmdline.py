import psutil
for pid in (8692,6484):
    try:
        p=psutil.Process(pid)
        print(pid, p.name(), p.cmdline())
    except Exception as e:
        print(pid, type(e).__name__, e)