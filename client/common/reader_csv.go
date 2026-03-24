package common

import (
	"bufio"
	"os"
	"strings"
	"io"
)

// ReaderCsv is responsible for reading the CSV file and providing records to the client
type ReaderCsv struct {
	file    *os.File
	scanner *bufio.Scanner
}

// NewReaderCsv opens the CSV file and initializes the ReaderCsv struct
func NewReaderCsv(path string) (*ReaderCsv, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, err
	}

	scanner := bufio.NewScanner(file)
	
	return &ReaderCsv{
		file:    file,
		scanner: scanner,
	}, nil
}

// ReadNext returns the next record from the CSV file as a slice of strings
func (r *ReaderCsv) ReadNext() ([]string, error) {
	if !r.scanNext() {
		if err := r.scanner.Err(); err != nil {
			return nil, err
		}
		return nil, io.EOF
	}

	line := r.scanner.Text()

	record := strings.Split(line, ",")

	return record, nil
}

// scanNext is a wrapper for the scanner
func (r *ReaderCsv) scanNext() bool {
	return r.scanner.Scan()
}

// Close releases the file resource
func (r *ReaderCsv) Close() error {
	return r.file.Close()
}