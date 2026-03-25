package common

import (
	"bytes"
	"encoding/binary"
	"fmt"
)

const (
	typeInt    = 1
	typeString = 2
	typeWinnersRequest  = 3
	ackErrorBatch   = 1
	sizeResponse = 1
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

// receiveBet reads a bet message from the protocol socket and returns a Bet struct with the received data
// The expected format of the message is the same as the one used in serializeBet, which is a TLV-like format
func (p *Protocol) receiveBet() (*Bet, error) {
	agency, err := p.readInt()
	if err != nil {
		return nil, err
	}
	name, err := p.readString()
	if err != nil {
		return nil, err
	}
	lastName, err := p.readString()
	if err != nil {
		return nil, err
	}
	document, err := p.readInt()
	if err != nil {
		return nil, err
	}
	birthDate, err := p.readString()
	if err != nil {
		return nil, err
	}
	number, err := p.readInt()
	if err != nil {
		return nil, err
	}
	return &Bet{
		Agency:    agency,
		FirstName: name,
		LastName:  lastName,
		Document:  document,
		BirthDate: birthDate,
		Number:    number,
	}, nil
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

// ReceiveResponse read the response byte from the server.
// If the received code is ackError or if there is a network failure, an error is returned
func (p *Protocol) ReceiveResponse() error {
	data, err := p.socket.Receive(sizeResponse)
	if err != nil {
		return fmt.Errorf("error reading response from server: %w", err)
	}

	code := data[0]
	if code == ackErrorBatch {
		return fmt.Errorf("the server reported an error while processing the batch")
	}

	return nil
}

// ReceiveWinners waits to receive the winners of the lottery from the server
// The format of the message is:
// | WINNER_COUNT (4 bytes) | WINNERS (N bytes) |
// Where WINNER_COUNT is the number of winners, and each winner is serialized in the same TLV-like format as the bets
func (p *Protocol) ReceiveWinners() []*Bet {
	// receive the number of winners first
	countBuf, err := p.socket.Receive(4)
	if err != nil {
		log.Errorf("action: receive_count_winners | result: fail | error: %v", err)
		return nil
	}
	winnerCount := binary.BigEndian.Uint32(countBuf)

	winners := make([]*Bet, 0, winnerCount)
	for i := uint32(0); i < winnerCount; i++ {
		winner, err := p.receiveBet()
		if err != nil {
			log.Errorf("action: receive_winners | result: fail | error: %v", err)
			return nil
		}
		winners = append(winners, winner)
	}

	return winners
}

// readInt reads an integer value from the protocol socket, expecting the TLV-like format for integers
func (p *Protocol) readInt() (int, error) {
	typeBuf, err := p.socket.Receive(1)
	if err != nil {
		return 0, err
	}
	if typeBuf[0] != typeInt {
		return 0, fmt.Errorf("expected TYPE_INT, got %d", typeBuf[0])
	}

	valueBuf, err := p.socket.Receive(4)
	if err != nil {
		return 0, err
	}

	return int(binary.BigEndian.Uint32(valueBuf)), nil
}

// readString reads a string value from the protocol socket, expecting the TLV-like format for strings
func (p *Protocol) readString() (string, error) {
	typeBuf, err := p.socket.Receive(1)
	if err != nil {
		return "", err
	}
	if typeBuf[0] != typeString {
		return "", fmt.Errorf("expected TYPE_STRING, got %d", typeBuf[0])
	}

	lengthBuf, err := p.socket.Receive(2)
	if err != nil {
		return "", err
	}
	length := binary.BigEndian.Uint16(lengthBuf)

	valueBuf, err := p.socket.Receive(int(length))
	if err != nil {
		return "", err
	}

	return string(valueBuf), nil
}

// SendWinnersRequest sends a request to the server to receive the winners of the lottery
// The message format is simply a single byte with the type code for the winners request
func (p *Protocol) SendWinnersRequest() error {
    data := []byte{typeWinnersRequest}
    return p.socket.Send(data)
}