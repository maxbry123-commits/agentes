package logger

import (
	"context"
	"fmt"

	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
)

type contextKey string

const (
	campaignIDKey contextKey = "campaign_id"
	agentNameKey  contextKey = "agent_name"
	techniqueKey  contextKey = "technique"
)

var global *zap.Logger

// Init initializes the global logger. Call once at startup.
func Init(level, format string) error {
	var cfg zap.Config

	switch format {
	case "json":
		cfg = zap.NewProductionConfig()
	default:
		cfg = zap.NewDevelopmentConfig()
		cfg.EncoderConfig.EncodeLevel = zapcore.CapitalColorLevelEncoder
	}

	switch level {
	case "debug":
		cfg.Level.SetLevel(zap.DebugLevel)
	case "info":
		cfg.Level.SetLevel(zap.InfoLevel)
	case "warn":
		cfg.Level.SetLevel(zap.WarnLevel)
	case "error":
		cfg.Level.SetLevel(zap.ErrorLevel)
	default:
		cfg.Level.SetLevel(zap.InfoLevel)
	}

	cfg.EncoderConfig.TimeKey = "timestamp"
	cfg.EncoderConfig.EncodeTime = zapcore.ISO8601TimeEncoder

	l, err := cfg.Build(zap.AddCallerSkip(1))
	if err != nil {
		return fmt.Errorf("building logger: %w", err)
	}

	global = l
	return nil
}

// Get returns the global logger.
func Get() *zap.Logger {
	if global == nil {
		// Fallback to nop logger if Init wasn't called
		global = zap.NewNop()
	}
	return global
}

// Sync flushes any buffered log entries. Call before program exit.
func Sync() {
	if global != nil {
		_ = global.Sync()
	}
}

// WithCampaignID returns a context with the campaign ID attached.
func WithCampaignID(ctx context.Context, id string) context.Context {
	return context.WithValue(ctx, campaignIDKey, id)
}

// WithAgentName returns a context with the agent name attached.
func WithAgentName(ctx context.Context, name string) context.Context {
	return context.WithValue(ctx, agentNameKey, name)
}

// WithTechnique returns a context with the technique name attached.
func WithTechnique(ctx context.Context, technique string) context.Context {
	return context.WithValue(ctx, techniqueKey, technique)
}

// FromContext returns a logger with all context fields attached.
func FromContext(ctx context.Context) *zap.Logger {
	l := Get()

	if id, ok := ctx.Value(campaignIDKey).(string); ok && id != "" {
		l = l.With(zap.String("campaign_id", id))
	}
	if name, ok := ctx.Value(agentNameKey).(string); ok && name != "" {
		l = l.With(zap.String("agent", name))
	}
	if tech, ok := ctx.Value(techniqueKey).(string); ok && tech != "" {
		l = l.With(zap.String("technique", tech))
	}

	return l
}

// Convenience functions that use the global logger

func Debug(msg string, fields ...zap.Field) { Get().Debug(msg, fields...) }
func Info(msg string, fields ...zap.Field)  { Get().Info(msg, fields...) }
func Warn(msg string, fields ...zap.Field)  { Get().Warn(msg, fields...) }
func Error(msg string, fields ...zap.Field) { Get().Error(msg, fields...) }
func Fatal(msg string, fields ...zap.Field) { Get().Fatal(msg, fields...) }
