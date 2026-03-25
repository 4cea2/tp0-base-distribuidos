package common

import (
	"io"
	"time"
	"os"
	"os/signal"
	"syscall"
	"github.com/op/go-logging"
)

const (
	pathCsv = "./data.csv"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
	BatchMaxAmount int
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	readerCsv *ReaderCsv
	socket *Socket
	protocol *Protocol
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	socket, err := NewSocket(config.ServerAddress)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			config.ID,
			err,
		)
		return nil
	}
	protocol := NewProtocol(socket)

	reader, err := NewReaderCsv(pathCsv)
	if err != nil {
		log.Errorf("action: init_reader | result: fail | error: %v", err)
			socket.Close()
		return nil
	}

	client := &Client{
		config: config,
		readerCsv: reader,
		socket: socket,
		protocol: protocol,
	}
	return client
}

// handleShutdown listens for SIGTERM and gracefully shuts down the client
func (c *Client) handleShutdown() {
	signalChannel := make(chan os.Signal, 1)
	signal.Notify(signalChannel, syscall.SIGTERM)

	go func() {
		signalReceived := <-signalChannel

		if c.socket != nil {
			c.socket.Close()
		}
		c.socket = nil

		log.Infof("action: shutdown | result: success | signal: %v | client_id: %v",
			signalReceived, c.config.ID,
		)

	}()
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() {
	c.handleShutdown()

	log.Infof("action: start_client_loop | result: success | client_id: %v", c.config.ID)
	
	// Process bets from .csv in batches and send them to the server, waiting for a response after each batch
	c.processAndSendBets()

	// After finishing sending bets, wait to receive the winners from the server and log the result
	c.handleWinners()

	// Close resources
	c.cleanup()

	log.Infof("action: client_finished | result: success | client_id: %v", c.config.ID)
}

func (c *Client) processAndSendBets() {
    batch := make([]*Bet, 0, c.config.BatchMaxAmount)

    for {
        record, err := c.readerCsv.ReadNext()
        if err == io.EOF {
            if len(batch) > 0 {
                c.sendBatchAndReceiveResponse(batch)
				batch = batch[:0]
            }
            c.sendBatchAndReceiveResponse([]*Bet{}) 
            log.Infof("action: end_of_file | result: success | client_id: %v", c.config.ID)
            break
        }
        
        if err != nil {
            log.Errorf("action: read_line | result: fail | error: %v", err)
            continue
        }

        bet, err := NewBet(c.config.ID, record)
        if err != nil {
            log.Errorf("action: create_bet | result: fail | error: %v", err)
            continue
        }

        batch = append(batch, bet)

        if len(batch) >= c.config.BatchMaxAmount {
            c.sendBatchAndReceiveResponse(batch)
            batch = batch[:0]
        }
    }
}

func (c *Client) handleWinners() {
    winners := c.protocol.ReceiveWinners()
    if winners != nil {
        log.Infof("action: consulta_ganadores | result: success | cant_ganadores: %d | client_id: %v", len(winners), c.config.ID)
    } else {
        log.Errorf("action: consulta_ganadores | result: fail | client_id: %v", c.config.ID)
    }
}

func (c *Client) cleanup() {
    if err := c.readerCsv.Close(); err != nil {
        log.Errorf("action: close_reader | result: fail | error: %v", err)
    }

    if c.socket != nil {
        if err := c.socket.Close(); err != nil {
            log.Errorf("action: close_socket | result: fail | error: %v", err)
        }
        c.socket = nil
    }
}

func (c *Client) sendBatchAndReceiveResponse(batch []*Bet) {
    if err := c.protocol.SendBatch(batch); err != nil {
        log.Errorf("action: send_batch | result: fail | size: %d | error: %v", len(batch), err)
        return
    } else {
		log.Infof("action: send_batch | result: success | size: %d | client_id: %v", len(batch), c.config.ID)
	}

    if err := c.protocol.ReceiveResponse(); err != nil {
		log.Errorf("action: receive_response | result: fail | error: %v", err)
    } else {
		log.Infof("action: receive_response | result: success | client_id: %v", c.config.ID)
	}
}
