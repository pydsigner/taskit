import sys


def get_ports(ports):
    if '-' in ports:
        start, stop = ports.split('-')
        return (p for p in range(int(start), int(stop) + 1))
    return (int(p) for p in ports.split(','))


if __name__ == '__main__':
    host, ports = sys.argv[1:]
    for port in get_ports(ports):
        print('%s:%s' % (host, port))
