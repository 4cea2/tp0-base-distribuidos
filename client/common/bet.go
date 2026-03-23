package common

import (
	"os"
	"strconv"
	"fmt"
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

// loadBetFromEnv reads, validates and parses env variables
func loadBetFromEnv() (string, string, int, string, int, error) {
	firstName := os.Getenv("NOMBRE")
	lastName := os.Getenv("APELLIDO")
	documentStr := os.Getenv("DOCUMENTO")
	birthDate := os.Getenv("NACIMIENTO")
	numberStr := os.Getenv("NUMERO")

	if firstName == "" || lastName == "" || documentStr == "" || birthDate == "" || numberStr == "" {
		return "", "", 0, "", 0, fmt.Errorf("missing required environment variables")
	}

	document, err := strconv.Atoi(documentStr)
	if err != nil {
		return "", "", 0, "", 0, fmt.Errorf("invalid DOCUMENTO: %w", err)
	}

	number, err := strconv.Atoi(numberStr)
	if err != nil {
		return "", "", 0, "", 0, fmt.Errorf("invalid NUMERO: %w", err)
	}

	return firstName, lastName, document, birthDate, number, nil
}

func NewBet(agency_str string) (*Bet, error) {
	firstName, lastName, document, birthDate, number, err := loadBetFromEnv()
	if err != nil {
		return nil, err
	}
	agency, err := strconv.Atoi(agency_str)
	if err != nil {
		return nil, fmt.Errorf("invalid agency ID: %w", err)
	}
	return &Bet{
		Agency:    agency,
		FirstName: firstName,
		LastName:  lastName,
		Document:  document,
		BirthDate: birthDate,
		Number:    number,
	}, nil
}