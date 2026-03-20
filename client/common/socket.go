package common

import (
	"net"
)

type Socket struct {
	conn net.Conn
}

// NewSocket creates a new socket TCP connection to the server address provided as a parameter 
// In case of failure, nil is returned
func NewSocket(serverAddress string) (*Socket, error) {
	conn, err := net.Dial("tcp", serverAddress)
	if err != nil {
		return nil, err
	}
	return &Socket{conn: conn}, nil
}

// Send send the data through the socket. In case of failure, error is returned
// For short write cases, this method will try to send the remaining data until all the data is sent or an error occurs
func (s *Socket) Send(data []byte) error {
	total := 0

	for total < len(data) {
		n, err := s.conn.Write(data[total:])
		if err != nil {
			return err
		}
		total += n
	}

	return nil
}


// Receive receives data from the socket. In case of failure, error is returned
// For short read cases, this method will try to receive the remaining data until all the data (size) is received or an error occurs
func (s *Socket) Receive(size int) ([]byte, error) {
	buf := make([]byte, size)
	total := 0

	for total < size {
		n, err := s.conn.Read(buf[total:])
		if err != nil {
			return nil, err
		}
		total += n
	}

	return buf, nil
}

// Close closes the socket connection. In case of failure, error is returned
func (s *Socket) Close() error {
	return s.conn.Close()
}