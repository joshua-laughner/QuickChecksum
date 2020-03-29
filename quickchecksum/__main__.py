from argparse import ArgumentParser
import hashlib
import sys


_default_alg = 'md5'


def compare_checksum(target_file, algorithm, given_checksum, verbose=False):
    file_hash = getattr(hashlib, algorithm)()
    with open(target_file, 'rb') as robj:
        file_hash.update(robj.read())

    computed_checksum = file_hash.hexdigest()
    matches = given_checksum == computed_checksum
    if verbose:
        return matches, computed_checksum
    else:
        return matches


def driver(file, checksum=None, algorithm=_default_alg, verbose=1):
    if checksum is None:
        checksum = sys.stdin.read().strip()
    matches, computed_checksum = compare_checksum(file, given_checksum=checksum, algorithm=algorithm, verbose=True)
    base_str = '{}: {}'.format(file, 'OK' if matches else 'FAILED')
    if verbose == 1:
        print(base_str)
    elif verbose > 1:
        print('{} (given {} vs. computed {})'.format(base_str, checksum, computed_checksum))

    return 0 if matches else 2


def parse_args():
    p = ArgumentParser(description='Verify the checksum for a single file')
    p.add_argument('file', help='The file to verify')
    p.add_argument('-c', '--checksum', help='The expected checksum for the file. If not given, it is to be provided '
                                            'via stdin')
    p.add_argument('-a', '--algorithm', default=_default_alg, choices=hashlib.algorithms_available,
                   help='Which algorithm to use for the hash. Default is %(default)s.')
    p.add_argument('-v', '--verbose', action='store_const', const=2, dest='verbose', default=1,
                   help='Print the given and computed checksum for manual verification')
    p.add_argument('-q', '--quiet', action='store_const', const=0, dest='verbose',
                   help='Silence all printing to the command line. The success or failure will only be communicated '
                        'by the exit code. 0 means the file\'s checksum matched, 2 means it did not.')

    return vars(p.parse_args())


def main():
    args = parse_args()
    ecode = driver(**args)
    sys.exit(ecode)


if __name__ == '__main__':
    main()
