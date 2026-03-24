package common

import (
	"bytes"
	"encoding/binary"
)

const (
	typeInt    = 1
	typeString = 2
	confirmationBetSize = 1
)

type Protocol struct {
	socket *Socket
}

// NewProtocol initializes a new protocol with the socket provided as a parameter
func NewProtocol(socket *Socket) *Protocol {
	return &Protocol{socket: socket}
}

// writeInt encodes an integer value in the buffer using the TLV-like format
func writeInt(buf *bytes.Buffer, value int) error {
	// TYPE
	if err := buf.WriteByte(typeInt); err != nil {
		return err
	}

	// VALUE
	return binary.Write(buf, binary.BigEndian, int32(value))
}

// writeString encodes a string value in the buffer using the TLV-like format
func writeString(buf *bytes.Buffer, value string) error {
	// TYPE
	if err := buf.WriteByte(typeString); err != nil {
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
// | TYPE (1 byte) | LENGTH (2 bytes, optional) | VALUE (N bytes) |
// TYPE (1 byte):
//   1 = int
//   2 = string
// LENGTH (2 bytes): is only used for the string type
//
// VALUE (N bytes):
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

// SendBet sends a bet message through the protocol socket
// In case of failure, error is returned
func (p *Protocol) sendBet(bet *Bet) error {
	data, err := serializeBet(bet)
	if err != nil {
		return err
	}

	return p.socket.Send(data)
}

// SendBatch sends a batch of bets to the server
// It first sends the number of bets as a uint32, followed by each bet serialized in the TLV-like format
// | BET_COUNT (4 bytes) | BETS (N bytes) |
func (p *Protocol) SendBatch(bets []*Bet) error {
    // serialize the batch size (number of bets)
    batchSize := uint32(len(bets))
    sizeBuf := make([]byte, 4)
    binary.BigEndian.PutUint32(sizeBuf, batchSize)

    // send the batch size first
    if err := p.socket.Send(sizeBuf); err != nil {
        return err
    }
    // serialize and send each bet in the batch
    for _, bet := range bets {
		data, err := serializeBet(bet) 
        if err != nil {
            return err
        }
        if err := p.socket.Send(data); err != nil {
            return err
        }
    }
    return nil
}