package common

import (
	"strconv"
	"fmt"
)

const (
	// Column indices for the CSV record
	firstNameIndex = 0
	lastNameIndex  = 1
	documentIndex  = 2
	birthDateIndex = 3
	numberIndex    = 4
)

// Bet struct that represents a bet to be sent to the server
type Bet struct {
	Agency    int
	FirstName string
	LastName  string
	Document  int
	BirthDate string
	Number    int
}

// NewBet creates a new Bet instance from the given agency string and CSV record
// It expects the record to have at least 5 columns: FirstName, LastName, Document, BirthDate, and Number
// The agency string is converted to an integer and assigned to the Agency field
// If any conversion fails, an error is returned
func NewBet(agencyStr string, record []string) (*Bet, error) {
	if len(record) < 5 {
		return nil, fmt.Errorf("registro incompleto: se esperaban 5 columnas, hay %d", len(record))
	}

	agency, err := strconv.Atoi(agencyStr)
	if err != nil {
		return nil, fmt.Errorf("error agency id: %w", err)
	}

	doc, err := strconv.Atoi(record[documentIndex])
	if err != nil {
		return nil, fmt.Errorf("error documento: %w", err)
	}

	num, err := strconv.Atoi(record[numberIndex])
	if err != nil {
		return nil, fmt.Errorf("error número apuesta: %w", err)
	}

	return &Bet{
		Agency:    agency,
		FirstName: record[firstNameIndex],
		LastName:  record[lastNameIndex],
		Document:  doc,
		BirthDate: record[birthDateIndex],
		Number:    num,
	}, nil
}