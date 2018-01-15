import io, os, shutil, unicodedata, datetime, sys

def remove_old_files(max_days):
    num_deleted = 0
    for root, ds, fs in os.walk('Routes'):
        for f in fs:
            name, ext = os.path.splitext(f)
            if ext == '.csv':
                if name == 'stopdata' or name == 'positioning':
                    continue
                timestamp = datetime.datetime.strptime(name, '%Y-%m-%d %H:%M:%S.%f')
                delta = datetime.datetime.now() - timestamp
                if delta.total_seconds() > (24 * 60 * 60 * max_days):
                    pathname = os.path.join(root, f)
                    os.remove(pathname)
                    num_deleted +=1
    return num_deleted

days = int(raw_input('Enter max age (days): '))
num_deleted = remove_old_files(days)
print '\n', days, ' files removed.'

