from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, RawDescriptionHelpFormatter
import hashlib
import os
import sys


_default_alg = 'md5'
_algs_by_length = {32: 'md5',
                   40: 'sha1',
                   56: 'sha224',
                   64: 'sha256',
                   96: 'sha384',
                   128: 'sha512'}


def guess_algorithm(checksum):
    n = len(checksum)
    try:
        return _algs_by_length[n]
    except KeyError:
        raise KeyError(f'Cannot infer an algorithm for a hash with {n} characters')


def get_checksum(target_file, algorithm):
    file_hash = getattr(hashlib, algorithm)()
    with open(target_file, 'rb') as robj:
        file_hash.update(robj.read())

    return file_hash.hexdigest()


def compare_checksum(target_file, algorithm, given_checksum):
    file_hash = getattr(hashlib, algorithm)()
    with open(target_file, 'rb') as robj:
        file_hash.update(robj.read())

    computed_checksum = get_checksum(target_file, algorithm)
    matches = given_checksum == computed_checksum
    return matches, computed_checksum


def compare_to_sum(file, checksum=None, algorithm=None, verbose=1):
    if algorithm is None:
        algorithm = guess_algorithm(checksum)
    if checksum is None:
        checksum = sys.stdin.read().strip()
    matches, computed_checksum = compare_checksum(file, given_checksum=checksum, algorithm=algorithm)
    base_str = '{}: {} ({})'.format(file, 'OK' if matches else 'FAILED', algorithm.upper())
    if verbose == 1:
        print(base_str)
    elif verbose > 1:
        print('{} (given {} vs. computed {})'.format(base_str, checksum, computed_checksum))

    return 0 if matches else 2


def _fit_file_path(n, filepath, other_file):
    if len(filepath) <= n:
        return filepath

    file_parts = filepath.split(os.sep)
    other_parts = other_file.split(os.sep)
    base_same = file_parts[-1] == other_parts[-1]
    if not base_same and len(file_parts[-1]) > n:
        # Prioritize showing as much of the basename as possible
        return os.path.join('...', file_parts[-1][:n-7] + '...')
    elif not base_same and len(file_parts[-1]) + len(file_parts[0]) + 5 > n:
        # If the first part of the directory plus the basename, two separators, and one '...'
        # wouldn't fit, just return the basename
        return file_parts[-1]
    elif not base_same or filepath == other_file:
        # If we can get at least one leading directory part in, then try to fit as much as possible
        # If both files are the same, then we also do this
        i = 0
        while i < len(file_parts):
            i += 1
            tmp_path = os.path.join(*file_parts[:i], '...', file_parts[-1])
            if len(tmp_path) > n:
                break
        return os.path.join(*file_parts[:i-1], '...', file_parts[-1])
    else:
        # If the base names are the same, find the first directory piece that's different and print
        # as much of the path as possible starting from there
        for i, (me,other) in enumerate(zip(file_parts, other_parts)):
            if me != other:
                break

        j = i
        while j < len(file_parts):
            j += 1
            tmp_path = os.path.join('...', *file_parts[i:j], '...')
            if len(tmp_path) > n:
                break

        if j == len(file_parts):
            tmp_path = os.path.join('...', *file_parts[i:j])
            if len(tmp_path) < n:
                return tmp_path
        return os.path.join('...', *file_parts[i:j-1], '...')



def _fit_checksums(n, cksum1, cksum2):
    if cksum1 == cksum2:
        if len(cksum1) > n:
            cksum1 = cksum1[:n-3] + '...'
            cksum2 = cksum2[:n-3] + '...'
    else:
        for i, (a,b) in enumerate(zip(cksum1, cksum2)):
            if a != b:
                break

        mstr = '({} match) ...'.format(i)
        nfree = n - len(mstr)
        if len(cksum1[i:]) <= nfree:
            cksum1 = cksum1[i:]
        else:
            cksum1 = cksum1[i:i+nfree-3] + '...'
        if len(cksum2[i:]) <= nfree:
            cksum2 = cksum2[i:]
        else:
            cksum2 = cksum2[i:i+nfree-3] + '...'

    return cksum1, cksum2


def _print_verbose_comparison(file1, file2, cksum1, cksum2, matches, algorithm):
    # Width must allow for three separators and four padding spaces
    twidth = os.get_terminal_size().columns
    max_col_width = int((twidth - 7)/2)

    # If all of the strings to be printed fit, then just make the column
    # big enough for the longest string
    max_str_len = max([len(file1), len(file2), len(cksum1), len(cksum2)])
    n = max_str_len if max_str_len < max_col_width else max_col_width
    nmid = 2*n + 5
    fmt = '| {{:^{0}}} | {{:^{0}}} |'.format(n)
    fmtmid = '|{{:^{0}}}|'.format(nmid)

    # Now the file paths: if both fit in the column, we can just print them.
    # If not, print as much that is different as we can, favoring the base
    # name if that is different.
    pretty_file1 = _fit_file_path(n, file1, file2)
    pretty_file2 = _fit_file_path(n, file2, file1)
    # Same for checksums
    pretty_sum1, pretty_sum2 = _fit_checksums(n, cksum1, cksum2)
    match_str = fmtmid.format(f'OK ({algorithm})' if matches else f'FAILED ({algorithm})')

    # Print the comparison table
    print(fmtmid.format('='*nmid))
    print(fmt.format('Original', 'New'))
    print(fmt.format('-'*n, '-'*n))
    print(fmt.format(pretty_file1, pretty_file2))
    print(fmt.format(pretty_sum1, pretty_sum2))
    print(fmtmid.format(''))
    print(match_str)
    print(fmtmid.format('='*nmid))
    

def compare_files(file, original, algorithm=None, verbose=1):
    if algorithm is None:
        algorithm = _default_alg
    original_sum = get_checksum(original, algorithm)
    matches, new_sum = compare_checksum(file, given_checksum=original_sum, algorithm=algorithm)
    if verbose == 1:
        print('{}: {} ({})'.format(file, 'OK' if matches else 'FAILED', algorithm.upper()))
    elif verbose > 1:
        _print_verbose_comparison(original, file, original_sum, new_sum, matches, algorithm.upper())

    return 0 if matches else 2


def _format_alg_list():
    # Create a table with three columns
    algs = sorted(hashlib.algorithms_available)
    n = max(len(a) for a in algs)
    fmt = '* {{:{}s}}  '.format(n)
    strings = ['    ']
    for i, a in enumerate(algs):
        strings.append(fmt.format(a))
        if i % 3 == 2:
            strings.append('\n    ')
    return ''.join(strings)


def parse_args():
    p = ArgumentParser(description='Verify the checksum for a single file', formatter_class=RawDescriptionHelpFormatter)
    p.add_argument('file', help='The file to verify')

    hash_len_str = '; '.join('{} = {}'.format(k,v) for k,v in _algs_by_length.items())
    p.add_argument('-a', '--algorithm', default=None, choices=hashlib.algorithms_available, metavar='ALGORITHM',
                   help=f'Which algorithm to use for the hash. When comparing two files using '
                        f'the --original flag, the default is {_default_alg}. When checking '
                        f'against an existing checksum, the default behavior is to guess the '
                        f'algorithm from the length of the checksum ({hash_len_str}). If the '
                        f'length is unexpected, an error occurs.')

    p.epilog = 'The algorithms available on this computer are:\n\n{}\n\nHowever, be aware that some require extra information and will not work.'.format(_format_alg_list())
    
    chk_grp = p.add_mutually_exclusive_group()
    chk_grp.add_argument('-c', '--checksum', help='The expected checksum for the file. If not given, it can be read from stdin ')
    chk_grp.add_argument('-o', '--original', help='An original file to compare the checksum against.')
    
    v_grp = p.add_mutually_exclusive_group()
    v_grp.add_argument('-v', '--verbose', action='store_const', const=2, dest='verbose', default=1,
                   help='Print the given and computed checksum for manual verification')
    v_grp.add_argument('-q', '--quiet', action='store_const', const=0, dest='verbose',
                   help='Silence all printing to the command line. The success or failure will only be communicated '
                        'by the exit code. 0 means the file\'s checksum matched, 2 means it did not. 1 indicates an error.')

    return vars(p.parse_args())


def driver(file, checksum=None, algorithm=_default_alg, original=None, verbose=1):
    if original is None:
        return compare_to_sum(file, checksum=checksum, algorithm=algorithm, verbose=verbose)
    else:
        return compare_files(file, original, algorithm=algorithm, verbose=verbose)


def main():
    args = parse_args()
    try:
        ecode = driver(**args)
    except Exception as err:
        print(f'ERROR: {str(err)}', file=sys.stderr)
        sys.exit(1)
    else:
        sys.exit(ecode)


if __name__ == '__main__':
    main()
