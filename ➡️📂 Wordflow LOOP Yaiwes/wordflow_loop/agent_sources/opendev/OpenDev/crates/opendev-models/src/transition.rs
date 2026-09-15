//! Transition validation for event-sourced state machines.

use thiserror::Error;

/// Errors that can occur when validating a state transition.
#[derive(Debug, Error)]
pub enum TransitionError {
    #[error("cannot {action} an archived session")]
    SessionArchived { action: String },
    #[error("session already archived")]
    AlreadyArchived,
    #[error("session is not archived")]
    NotArchived,
    #[error("fork point {point} is out of range (session has {message_count} messages)")]
    ForkPointOutOfRange { point: usize, message_count: usize },
    #[error("title cannot be empty")]
    EmptyTitle,
    #[error("invalid transition: {reason}")]
    Invalid { reason: String },
}

/// Trait for validating state transitions.
///
/// Implementors check whether a given event/action is valid given the current state.
pub trait ValidateTransition<E> {
    fn validate_transition(&self, event: &E) -> Result<(), TransitionError>;
}

#[cfg(test)]
#[path = "transition_tests.rs"]
mod tests;
