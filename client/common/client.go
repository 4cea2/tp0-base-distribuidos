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

	batch := make([]*Bet, 0, c.config.BatchMaxAmount)

	log.Infof("action: start_client_loop | result: success | client_id: %v", c.config.ID)
	for {
		record_bet, err := c.readerCsv.ReadNext()
		if err == io.EOF {
			if len(batch) > 0 {
				c.sendBatch(batch)
			}
			log.Infof("action: end_of_file | result: success | client_id: %v", c.config.ID)
			break
		}
		if err != nil {
			log.Errorf("action: read_line | result: fail | error: %v", err)
			continue 
		}

		bet, err := NewBet(c.config.ID, record_bet)
		if err != nil {
			log.Errorf("action: create_bet | result: fail | client_id: %v | error: %v", c.config.ID, err)
			continue 
		}
		
		batch = append(batch, bet)

		if len(batch) == c.config.BatchMaxAmount {
			c.sendBatch(batch)
			batch = batch[:0]
		}
	}
	if c.socket != nil {
		if err := c.socket.Close(); err != nil {
			log.Errorf("action: close_socket | result: fail | error: %v", err)
		}
		c.socket = nil
		log.Infof("action: close_socket | result: success | client_id: %v", c.config.ID)
	}

	if err := c.readerCsv.Close(); err != nil {
		log.Errorf("action: close_reader | result: fail | error: %v", err)
	}
	log.Infof("action: close_reader | result: success | client_id: %v", c.config.ID)

	
	log.Infof("action: client_finished | result: success | client_id: %v", c.config.ID)
}

func (c *Client) sendBatch(batch []*Bet) {
    if err := c.protocol.SendBatch(batch); err != nil {
        log.Errorf("action: send_batch | result: fail | size: %d | error: %v", len(batch), err)
        return
    }
	log.Infof("action: send_batch | result: success | size: %d | client_id: %v", len(batch), c.config.ID)
}

