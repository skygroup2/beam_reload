import os


def find_beam(app, src_dir, dst_dir, name):
    rel = '%s/_build/prod/rel/%s/' % (src_dir, app)
    fn = 'Elixir.%s.beam' % name
    if name[0:1] == ':':
        fn = '%s.beam' % name[1:]
    fn_abs = None
    for root, _dirs, files in os.walk(rel):
        if fn_abs is not None:
            break
        for file in files:
            if file == fn:
                fn_abs = os.path.join(root, file)
                break
    sp = len(rel)
    print(fn_abs)
    if fn_abs is not None:
        fn_dabs = '%s/%s' % (dst_dir, fn_abs[sp:])
        return fn_abs, fn_dabs
    else:
        raise Exception('App %s, module %s is wrong' % (app, name))