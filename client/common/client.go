package common

import (
	"fmt"
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
	stopChannel chan bool
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	var socket *Socket
	client := &Client{
		config: config,
		socket: socket,
		stopChannel: make(chan bool, 1),
	}
	return client
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() {
	// Create a channel to listen for termination signals
	signalChannel := make(chan os.Signal, 1)
	// Notify the channel on SIGTERM signal
	signal.Notify(signalChannel, syscall.SIGTERM)

	// Start a goroutine to handle termination signals
	go func() {
		// Block until a signal is received
		signalReceived := <- signalChannel
		if c.socket != nil {
			c.socket.Close()
		}
		log.Infof("action: shutdown | result: success | signal: %v | client_id: %v", signalReceived, c.config.ID)
		// Send a notification to the main loop to stop it
		c.stopChannel <- true
	}()

	// There is an autoincremental msgID to identify every message sent
	// Messages if the message amount threshold has not been surpassed
	for msgID := 1; msgID <= c.config.LoopAmount; msgID++ {
		select {
		case <- c.stopChannel:
			// If a termination signal is received, the loop is interrupted
			log.Infof("action: loop_interrupted | result: success | client_id: %v", c.config.ID)
			return
		default:
			var err error
			c.socket, err = NewSocket(c.config.ServerAddress)
			if err != nil {
				log.Criticalf(
					"action: connect | result: fail | client_id: %v | error: %v",
					c.config.ID,
					err,
				)
			}

			msg := fmt.Sprintf("[CLIENT %v] Message N°%v\n", c.config.ID, msgID)
			c.socket.Send([]byte(msg))
			data, err := c.socket.Receive(len(msg))
			msg = string(data)
			c.socket.Close()

			if err != nil {
				log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v",
					c.config.ID,
					err,
				)
				return
			}

			log.Infof("action: receive_message | result: success | client_id: %v | msg: %v",
				c.config.ID,
				msg,
			)

			// Wait a time between sending one message and the next one
			time.Sleep(c.config.LoopPeriod)
		}
	}
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}

