// Copyright 2024 The gVisor Authors.
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

// Package vllm_test contains TPU-based vllm tests.
package vllm_test

import (
	"context"
	"fmt"
	"strings"
	"testing"
	"time"

	"gvisor.dev/gvisor/pkg/test/dockerutil"
	"gvisor.dev/gvisor/test/tpu/vllm"
)

func TestVLLM(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
	defer cancel()
	llm, err := vllm.NewDocker(ctx, dockerutil.MakeContainer(ctx, t), t)
	if err != nil {
		t.Fatalf("Failed to start vLLM: %v", err)
	}

	// Basic "math" test.
	t.Run("Math", func(t *testing.T) {
		prompt := vllm.ZeroTemperaturePrompt("What is 2+2? Reply with only the number.")
		// We use PromptUntil because LLMs can be flaky.
		_, err := llm.PromptUntil(ctx, prompt, func(p *vllm.Prompt, r *vllm.FullResponse) (*vllm.Prompt, error) {
			defer p.RaiseTemperature()
			if strings.Contains(r.Text(), "4") {
				return nil, nil
			}
			return p, fmt.Errorf("expected 4, got %q", r.Text())
		})
		if err != nil {
			t.Errorf("Math test failed: %v", err)
		}
	})

	// Basic "knowledge" test.
	t.Run("Knowledge", func(t *testing.T) {
		prompt := vllm.ZeroTemperaturePrompt("What is the capital of France? Reply with only the name of the city.")
		_, err := llm.PromptUntil(ctx, prompt, func(p *vllm.Prompt, r *vllm.FullResponse) (*vllm.Prompt, error) {
			defer p.RaiseTemperature()
			if strings.Contains(strings.ToLower(r.Text()), "paris") {
				return nil, nil
			}
			return p, fmt.Errorf("expected Paris, got %q", r.Text())
		})
		if err != nil {
			t.Errorf("Knowledge test failed: %v", err)
		}
	})
}
