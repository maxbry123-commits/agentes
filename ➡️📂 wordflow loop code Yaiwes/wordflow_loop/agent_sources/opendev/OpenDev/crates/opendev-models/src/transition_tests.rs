use super::*;

#[test]
fn test_transition_error_display_session_archived() {
    let err = TransitionError::SessionArchived {
        action: "add message to".to_string(),
    };
    assert_eq!(err.to_string(), "cannot add message to an archived session");
}

#[test]
fn test_transition_error_display_already_archived() {
    let err = TransitionError::AlreadyArchived;
    assert_eq!(err.to_string(), "session already archived");
}

#[test]
fn test_transition_error_display_not_archived() {
    let err = TransitionError::NotArchived;
    assert_eq!(err.to_string(), "session is not archived");
}

#[test]
fn test_transition_error_display_fork_point_out_of_range() {
    let err = TransitionError::ForkPointOutOfRange {
        point: 10,
        message_count: 5,
    };
    assert_eq!(
        err.to_string(),
        "fork point 10 is out of range (session has 5 messages)"
    );
}

#[test]
fn test_transition_error_display_empty_title() {
    let err = TransitionError::EmptyTitle;
    assert_eq!(err.to_string(), "title cannot be empty");
}

#[test]
fn test_transition_error_display_invalid() {
    let err = TransitionError::Invalid {
        reason: "something went wrong".to_string(),
    };
    assert_eq!(err.to_string(), "invalid transition: something went wrong");
}

/// Verify the trait can be implemented for a simple type.
#[test]
fn test_validate_transition_trait_implementable() {
    struct DummyState {
        locked: bool,
    }
    enum DummyEvent {
        Lock,
        Unlock,
    }
    impl ValidateTransition<DummyEvent> for DummyState {
        fn validate_transition(&self, event: &DummyEvent) -> Result<(), TransitionError> {
            match event {
                DummyEvent::Lock if self.locked => Err(TransitionError::Invalid {
                    reason: "already locked".to_string(),
                }),
                DummyEvent::Unlock if !self.locked => Err(TransitionError::Invalid {
                    reason: "not locked".to_string(),
                }),
                _ => Ok(()),
            }
        }
    }

    let state = DummyState { locked: false };
    assert!(state.validate_transition(&DummyEvent::Lock).is_ok());
    assert!(state.validate_transition(&DummyEvent::Unlock).is_err());

    let state = DummyState { locked: true };
    assert!(state.validate_transition(&DummyEvent::Lock).is_err());
    assert!(state.validate_transition(&DummyEvent::Unlock).is_ok());
}
