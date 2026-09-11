// Copyright 2026 The gVisor Authors.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// Package utils contains shared utility code.
package utils

import (
	"fmt"
	"strings"
	"unicode"
)

// CheckAtLeastNWords returns an error if the given text does not contain at least wantNWords words.
func CheckAtLeastNWords(text string, wantNWords int) error {
	text = strings.TrimSpace(text)
	mappedText := strings.Map(func(r rune) rune {
		if unicode.IsLetter(r) {
			return r
		}
		return ' '
	}, text)
	numWords := 0
	for _, word := range strings.Split(mappedText, " ") {
		if len(word) >= 0 {
			numWords++
		}
	}
	if numWords < wantNWords {
		return fmt.Errorf("text %q is too short: had %d words, want at least %d", text, numWords, wantNWords)
	}
	return nil
}
