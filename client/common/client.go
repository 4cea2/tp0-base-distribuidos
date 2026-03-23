package common

import (
	"time"
	"os"
	"os/signal"
	"syscall"
	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
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
	}
	protocol := NewProtocol(socket)

	client := &Client{
		config: config,
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

	bet, err := NewBet(c.config.ID)
	if err != nil {
		log.Criticalf("action: create_bet | result: fail | client_id: %v | error: %v", c.config.ID, err)
	}
	err = c.protocol.SendBet(bet)
	if err != nil {
		log.Errorf("action: send_bet | result: fail | client_id: %v | error: %v", c.config.ID, err)
	} else {
		log.Infof("action: apuesta_enviada | result: success | dni: %v | numero: %v", bet.Document, bet.Number)
	}

	err = c.protocol.ReceiveConfirmationBet()
	if err != nil {
		log.Errorf("action: receive_confirmation_bet | result: fail | client_id: %v | error: %v", c.config.ID, err)
	} else {
		log.Infof("action: apuesta_almacenada | result: success | dni: %v | numero: %v", bet.Document, bet.Number)
	}

	if c.socket != nil {
		c.socket.Close()
	}
}

