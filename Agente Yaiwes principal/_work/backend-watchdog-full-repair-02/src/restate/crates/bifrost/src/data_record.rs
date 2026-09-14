// Copyright (c) 2023 - 2026 Restate Software, Inc., Restate GmbH.
// All rights reserved.
//
// Use of this software is governed by the Business Source License
// included in the LICENSE file.
//
// As of the Change Date specified in that file, in accordance with
// the Business Source License, use of this software will be governed
// by the Apache License, Version 2.0.

use restate_clock::time::NanosSinceEpoch;
use restate_platform::memory::EstimatedMemorySize;
use restate_types::logs::{KeyFilter, Keys, Lsn, MatchKeyQuery};
use restate_types::storage::PolyBytes;

use crate::{LogEntry, MaybeRecord};

/// Error returned when a [`LogEntry`] is not a data record.
pub enum DataRecordError<S> {
    /// The entry was filtered out.
    Filtered {
        /// First covered sequence number.
        from: S,
        /// Last covered sequence number, inclusive.
        to: S,
    },
    /// The entry covers data that is known to be lost.
    DataLoss {
        /// First covered sequence number.
        from: S,
        /// Last covered sequence number, inclusive.
        to: S,
    },
    /// The entry was trimmed.
    Trimmed {
        /// First covered sequence number.
        from: S,
        /// Last covered sequence number, inclusive.
        to: S,
    },
}

impl<S: Copy> TryFrom<LogEntry<S>> for DataRecord<PolyBytes, S> {
    type Error = DataRecordError<S>;

    fn try_from(value: LogEntry<S>) -> Result<Self, Self::Error> {
        let (seq, record) = value.dissolve();
        match record {
            MaybeRecord::TrimGap(gap) => Err(DataRecordError::Trimmed {
                from: seq,
                to: gap.to,
            }),
            MaybeRecord::Filtered(gap) => Err(DataRecordError::Filtered {
                from: seq,
                to: gap.to,
            }),
            MaybeRecord::DataLoss(gap) => Err(DataRecordError::DataLoss {
                from: seq,
                to: gap.to,
            }),
            MaybeRecord::Data(record) => {
                let (created_at, inner, keys) = record.dissolve();
                Ok(Self {
                    seq,
                    created_at,
                    keys,
                    inner,
                })
            }
        }
    }
}

/// A log data record with the metadata needed for ordering and key filtering.
#[derive(Clone)]
pub struct DataRecord<M, S = Lsn> {
    seq: S,
    created_at: NanosSinceEpoch,
    keys: Keys,
    inner: M,
}

impl<M, S: Copy> DataRecord<M, S> {
    /// Builds a data record from its parts.
    pub fn new(created_at: NanosSinceEpoch, keys: Keys, seq: S, inner: M) -> Self {
        Self {
            seq,
            created_at,
            keys,
            inner,
        }
    }

    /// Timestamp attached to the record.
    #[inline]
    pub const fn created_at(&self) -> NanosSinceEpoch {
        self.created_at
    }

    /// Keys used for key-filter matching.
    #[inline]
    pub const fn keys(&self) -> &Keys {
        &self.keys
    }

    /// Sequence number of the record.
    #[inline]
    pub const fn seq(&self) -> S {
        self.seq
    }

    /// Payload of the record.
    #[inline]
    pub const fn inner(&self) -> &M {
        &self.inner
    }

    /// Consumes the record and returns its payload.
    #[inline]
    pub fn into_inner(self) -> M {
        self.inner
    }

    /// Transforms the payload while preserving sequence number, timestamp, and keys.
    pub fn map<B>(self, f: impl FnOnce(M) -> B) -> DataRecord<B, S> {
        DataRecord {
            seq: self.seq,
            created_at: self.created_at,
            keys: self.keys,
            inner: f(self.inner),
        }
    }

    /// Fallibly transforms the payload while preserving sequence number, timestamp, and keys.
    pub fn try_map<B, E>(self, f: impl FnOnce(M) -> Result<B, E>) -> Result<DataRecord<B, S>, E> {
        let body = f(self.inner)?;

        Ok(DataRecord {
            seq: self.seq,
            created_at: self.created_at,
            keys: self.keys,
            inner: body,
        })
    }
}

impl<M, S> AsRef<M> for DataRecord<M, S> {
    fn as_ref(&self) -> &M {
        &self.inner
    }
}

impl<M, S> AsMut<M> for DataRecord<M, S> {
    fn as_mut(&mut self) -> &mut M {
        &mut self.inner
    }
}

impl<M, S> MatchKeyQuery for DataRecord<M, S> {
    fn matches_key_query(&self, query: &KeyFilter) -> bool {
        self.keys.matches_key_query(query)
    }
}

impl<M: EstimatedMemorySize, S> EstimatedMemorySize for DataRecord<M, S> {
    fn estimated_memory_size(&self) -> usize {
        self.inner.estimated_memory_size()
    }
}
