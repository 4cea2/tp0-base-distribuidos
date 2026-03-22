package common

import (
	"bytes"
	"encoding/binary"
)

const (
	TypeInt    = 1
	TypeString = 2
)

type Protocol struct {
	socket *Socket
}

// NewProtocol initializes a new protocol with the socket provided as a parameter
func NewProtocol(socket *Socket) *Protocol {
	return &Protocol{socket: socket}
}

// writeInt writes an int field as:
func writeInt(buf *bytes.Buffer, value int) error {
	// TYPE
	if err := buf.WriteByte(TypeInt); err != nil {
		return err
	}

	// VALUE
	return binary.Write(buf, binary.BigEndian, int32(value))
}

func writeString(buf *bytes.Buffer, value string) error {
	// TYPE
	if err := buf.WriteByte(TypeString); err != nil {
		return err
	}

	// LENGTH
	length := uint16(len(value))
	if err := binary.Write(buf, binary.BigEndian, length); err != nil {
		return err
	}

	// VALUE
	_, err := buf.Write([]byte(value))
	return err
}

// serialize Bet using a format similar to TLV:
// TYPE (1 byte):
//   1 = int
//   2 = string
// LENGTH (2 bytes): is only used for the string type
//
// VALUE (dinamic size):
//  For int type, the value is 4 bytes, and for string type, the value is the length of the string in bytes
// 
// ORDER:
// Agency → FirstName → LastName → Document → BirthDate → Number
// 
// EXAMPLE:
// [01][00 00 00 01]           // Agency = 1 (int32)
// [02][00 10]Santiago Lionel  // FirstName (length = 16)
// [02][00 05]Lorca            // LastName (length = 5)
// [01][01 D7 8F 91]           // Document = 30904465 (int32)
// [02][00 0A]1999-03-17       // BirthDate (length = 10)
// [01][00 00 1D 96]           // Number = 7574 (int32)
func serializeBet(bet *Bet) ([]byte, error) {
	var buf bytes.Buffer

	if err := writeInt(&buf, bet.Agency); err != nil {
		return nil, err
	}
	if err := writeString(&buf, bet.FirstName); err != nil {
		return nil, err
	}
	if err := writeString(&buf, bet.LastName); err != nil {
		return nil, err
	}
	if err := writeInt(&buf, bet.Document); err != nil {
		return nil, err
	}
	if err := writeString(&buf, bet.BirthDate); err != nil {
		return nil, err
	}
	if err := writeInt(&buf, bet.Number); err != nil {
		return nil, err
	}

	return buf.Bytes(), nil
}

// SendBet sends a bet message through the protocol socket.
// In case of failure, error is returned
func (p *Protocol) SendBet(bet *Bet) error {
	data, err := serializeBet(bet)
	if err != nil {
		return err
	}

	return p.socket.Send(data)
}
