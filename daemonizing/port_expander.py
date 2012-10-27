import sys


def get_ports(ports):
    """
    Ports should one of:
      'number'
      'number,number2,number3...'
      'number-number2'
    """
    if '-' in ports:
        # example: '10-15' at this point
        start, stop = ports.split('-')
        # start, stop = '10', '15'
        # return range(10, 16) --> iter([10, 11, 12, 13, 14, 15])
        return range(int(start), int(stop) + 1)
    # Simply int each port that is split out:
    # '10,11,12' --> ['10', '11', '12'] --> iter([10, 11, 12])
    return (int(p) for p in ports.split(','))


if __name__ == '__main__':
    host, ports = sys.argv[1:]
    for port in get_ports(ports):
        print('%s:%s' % (host, port))
