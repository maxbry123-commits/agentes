"""Trusted Circles: Web-of-Trust-based skill ecosystem.

Loest das Ecosystem-Problem: P2P-Skills sind sicher, aber ohne
kritische Masse nutzlos. Trusted Circles schaffen kleine,
vertrauenswuerdige Peer-Gruppen (aehnlich PGP Web-of-Trust):

  - Kreise: Geschlossene Gruppen mit gegenseitigem Vertrauen
  - Kuratierte Sammlungen: Review-basierte Skill-Empfehlungen
  - Reputation-Boost: Circle-Mitgliedschaft erhoeht Trust
  - Import-Filter: Nur Skills aus vertrauten Kreisen

Architektur:
  TrustedCircle → Peer-Gruppe mit Invite-System
  CuratedCollection → Gepruefte Skill-Sammlung
  CircleManager → Verwaltung + Integration mit SkillExchange

Bibel-Referenz: §13 (P2P-Oekosystem -- Circle-Erweiterung)
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from cognithor.utils.logging import get_logger

log = get_logger(__name__)


# ============================================================================
# Enums
# ============================================================================


class CircleRole(Enum):
    """Role of a member in a circle."""

    OWNER = "owner"  # Creator, can do everything
    ADMIN = "admin"  # Can manage members + curate skills
    MEMBER = "member"  # Can share + install skills
    OBSERVER = "observer"  # Can only install skills, not share


class InviteStatus(Enum):
    """Status of a circle invitation."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REVOKED = "revoked"


class ReviewVerdict(Enum):
    """Result of a skill review."""

    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_CHANGES = "needs_changes"


# ============================================================================
# Data Models
# ============================================================================


@dataclass
class CircleMember:
    """Member of a trusted circle."""

    peer_id: str
    display_name: str = ""
    role: CircleRole = CircleRole.MEMBER
    joined_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    invited_by: str = ""  # Peer ID of the inviter
    skills_shared: int = 0
    skills_installed: int = 0

    @property
    def can_share(self) -> bool:
        return self.role in (CircleRole.OWNER, CircleRole.ADMIN, CircleRole.MEMBER)

    @property
    def can_manage(self) -> bool:
        return self.role in (CircleRole.OWNER, CircleRole.ADMIN)

    @property
    def can_curate(self) -> bool:
        return self.role in (CircleRole.OWNER, CircleRole.ADMIN)


@dataclass
class CircleInvite:
    """Invitation to a trusted circle."""

    invite_id: str
    circle_id: str
    inviter_id: str  # Who invites
    invitee_id: str  # Who is invited
    role: CircleRole = CircleRole.MEMBER
    status: InviteStatus = InviteStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    message: str = ""
    expires_hours: int = 72


@dataclass
class SkillReview:
    """Review of a skill in a curated collection."""

    reviewer_id: str  # Peer ID of the reviewer
    package_id: str
    verdict: ReviewVerdict
    comment: str = ""
    reviewed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    security_checked: bool = False
    test_passed: bool = False


@dataclass
class CuratedSkill:
    """A curated skill in a collection."""

    package_id: str
    name: str
    description: str = ""
    category: str = ""
    reviews: list[SkillReview] = field(default_factory=list)
    added_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    added_by: str = ""  # Peer ID

    @property
    def approval_count(self) -> int:
        return sum(1 for r in self.reviews if r.verdict == ReviewVerdict.APPROVED)

    @property
    def rejection_count(self) -> int:
        return sum(1 for r in self.reviews if r.verdict == ReviewVerdict.REJECTED)

    @property
    def is_approved(self) -> bool:
        """At least 2 approvals and no unresolved rejections."""
        return self.approval_count >= 2 and self.rejection_count == 0


# ============================================================================
# TrustedCircle
# ============================================================================


@dataclass
class TrustedCircle:
    """Ein vertrauenswuerdiger Kreis von Peers.

    Funktioniert wie ein PGP Web-of-Trust:
    - Geschlossene Gruppe mit Einladungssystem
    - Mitglieder vertrauen einander automatisch
    - Geteilte Skills erhalten Reputation-Boost
    - Circle-Name wird als Namespace fuer Skills verwendet
    """

    circle_id: str
    name: str
    description: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Members
    members: dict[str, CircleMember] = field(default_factory=dict)

    # Invitations
    invites: dict[str, CircleInvite] = field(default_factory=dict)

    # Curated skills
    curated_skills: dict[str, CuratedSkill] = field(default_factory=dict)

    # Settings
    require_review: bool = True  # Skills must be reviewed
    min_reviews_for_approval: int = 2
    auto_share_approved: bool = True  # Automatically share approved skills with all
    max_members: int = 50

    # ── Mitglieder-Verwaltung ────────────────────────────────────

    def add_member(
        self,
        peer_id: str,
        display_name: str = "",
        role: CircleRole = CircleRole.MEMBER,
        invited_by: str = "",
    ) -> CircleMember | None:
        """Add a member."""
        if peer_id in self.members:
            return None  # Already a member
        if len(self.members) >= self.max_members:
            return None  # Full

        member = CircleMember(
            peer_id=peer_id,
            display_name=display_name,
            role=role,
            invited_by=invited_by,
        )
        self.members[peer_id] = member
        log.info("circle_member_added", circle=self.name, peer=peer_id, role=role.value)
        return member

    def remove_member(self, peer_id: str, removed_by: str = "") -> bool:
        """Remove a member."""
        member = self.members.get(peer_id)
        if not member:
            return False

        # Owner cannot be removed
        if member.role == CircleRole.OWNER:
            return False

        del self.members[peer_id]
        log.info("circle_member_removed", circle=self.name, peer=peer_id, by=removed_by)
        return True

    def update_role(self, peer_id: str, new_role: CircleRole) -> bool:
        """Change the role of a member."""
        member = self.members.get(peer_id)
        if not member:
            return False
        if member.role == CircleRole.OWNER and new_role != CircleRole.OWNER:
            return False  # Owner role cannot be changed
        member.role = new_role
        return True

    def is_member(self, peer_id: str) -> bool:
        return peer_id in self.members

    def get_member(self, peer_id: str) -> CircleMember | None:
        return self.members.get(peer_id)

    @property
    def member_count(self) -> int:
        return len(self.members)

    @property
    def owner_id(self) -> str:
        for m in self.members.values():
            if m.role == CircleRole.OWNER:
                return m.peer_id
        return ""

    # ── Einladungen ──────────────────────────────────────────────

    def create_invite(
        self,
        inviter_id: str,
        invitee_id: str,
        role: CircleRole = CircleRole.MEMBER,
        message: str = "",
    ) -> CircleInvite | None:
        """Create an invitation."""
        inviter = self.members.get(inviter_id)
        if not inviter or not inviter.can_manage:
            return None  # No permission

        if invitee_id in self.members:
            return None  # Already a member

        invite_id = hashlib.sha256(
            f"{self.circle_id}:{invitee_id}:{datetime.now(UTC).isoformat()}".encode()
        ).hexdigest()[:16]

        invite = CircleInvite(
            invite_id=invite_id,
            circle_id=self.circle_id,
            inviter_id=inviter_id,
            invitee_id=invitee_id,
            role=role,
            message=message,
        )
        self.invites[invite_id] = invite
        log.info("circle_invite_created", circle=self.name, invitee=invitee_id)
        return invite

    def accept_invite(self, invite_id: str) -> CircleMember | None:
        """Accept an invitation."""
        invite = self.invites.get(invite_id)
        if not invite or invite.status != InviteStatus.PENDING:
            return None

        invite.status = InviteStatus.ACCEPTED
        return self.add_member(
            invite.invitee_id,
            role=invite.role,
            invited_by=invite.inviter_id,
        )

    def reject_invite(self, invite_id: str) -> bool:
        """Reject an invitation."""
        invite = self.invites.get(invite_id)
        if not invite or invite.status != InviteStatus.PENDING:
            return False
        invite.status = InviteStatus.REJECTED
        return True

    def pending_invites(self) -> list[CircleInvite]:
        return [i for i in self.invites.values() if i.status == InviteStatus.PENDING]

    # ── Kuratierung ──────────────────────────────────────────────

    def submit_skill(
        self,
        package_id: str,
        name: str,
        submitted_by: str,
        description: str = "",
        category: str = "",
    ) -> CuratedSkill | None:
        """Submit a skill for curation."""
        member = self.members.get(submitted_by)
        if not member or not member.can_share:
            return None

        if package_id in self.curated_skills:
            return None  # Already submitted

        skill = CuratedSkill(
            package_id=package_id,
            name=name,
            description=description,
            category=category,
            added_by=submitted_by,
        )
        self.curated_skills[package_id] = skill
        member.skills_shared += 1

        log.info("circle_skill_submitted", circle=self.name, skill=name, by=submitted_by)
        return skill

    def review_skill(
        self,
        package_id: str,
        reviewer_id: str,
        verdict: ReviewVerdict,
        comment: str = "",
        security_checked: bool = False,
        test_passed: bool = False,
    ) -> SkillReview | None:
        """Review a submitted skill."""
        member = self.members.get(reviewer_id)
        if not member or not member.can_curate:
            return None

        skill = self.curated_skills.get(package_id)
        if not skill:
            return None

        # Cannot review own submission
        if skill.added_by == reviewer_id:
            return None

        review = SkillReview(
            reviewer_id=reviewer_id,
            package_id=package_id,
            verdict=verdict,
            comment=comment,
            security_checked=security_checked,
            test_passed=test_passed,
        )
        skill.reviews.append(review)

        log.info(
            "circle_skill_reviewed",
            circle=self.name,
            skill=skill.name,
            verdict=verdict.value,
            reviewer=reviewer_id,
        )
        return review

    def approved_skills(self) -> list[CuratedSkill]:
        """All approved skills."""
        if not self.require_review:
            return list(self.curated_skills.values())
        return [s for s in self.curated_skills.values() if s.is_approved]

    def pending_reviews(self) -> list[CuratedSkill]:
        """Skills that still need reviews."""
        return [
            s for s in self.curated_skills.values() if not s.is_approved and s.rejection_count == 0
        ]


# ============================================================================
# CuratedCollection
# ============================================================================


@dataclass
class CuratedCollection:
    """Eine thematische Sammlung kuratierter Skills.

    Kann ueber Circle-Grenzen hinweg geteilt werden.
    Beispiele: "Versicherungs-Tools", "Developer-Utilities",
               "Familien-Helfer"
    """

    collection_id: str
    name: str
    description: str = ""
    maintainer_id: str = ""  # Peer ID des Kurators
    tags: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)  # Package-IDs
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    public: bool = False  # Publicly visible?

    def add_skill(self, package_id: str) -> bool:
        if package_id in self.skills:
            return False
        self.skills.append(package_id)
        return True

    def remove_skill(self, package_id: str) -> bool:
        if package_id not in self.skills:
            return False
        self.skills.remove(package_id)
        return True

    @property
    def skill_count(self) -> int:
        return len(self.skills)


# ============================================================================
# CircleManager
# ============================================================================


class CircleManager:
    """Manage Trusted Circles and integrate them with the ecosystem.

    Verantwortlich fuer:
    - Circle CRUD
    - Reputation-Boost fuer Circle-Mitglieder
    - Import-Filter (nur Skills aus vertrauten Kreisen)
    - Kuratierte Sammlungen
    - Discovery (welche Circles gibt es?)
    """

    # Reputation boost when skill is from own circle
    CIRCLE_REPUTATION_BOOST = 3.0
    # Maximum circles per peer
    MAX_CIRCLES_PER_PEER = 10

    def __init__(self) -> None:
        self._circles: dict[str, TrustedCircle] = {}
        self._collections: dict[str, CuratedCollection] = {}
        self._peer_circles: dict[str, set[str]] = {}  # peer_id → set(circle_id)

    # ── Circle CRUD ──────────────────────────────────────────────

    def create_circle(
        self,
        name: str,
        owner_id: str,
        owner_name: str = "",
        description: str = "",
        **kwargs: Any,
    ) -> TrustedCircle:
        """Create a new trusted circle."""
        circle_id = hashlib.sha256(
            f"{name}:{owner_id}:{datetime.now(UTC).isoformat()}".encode()
        ).hexdigest()[:12]

        circle = TrustedCircle(
            circle_id=circle_id,
            name=name,
            description=description,
            **kwargs,
        )
        circle.add_member(owner_id, display_name=owner_name, role=CircleRole.OWNER)

        self._circles[circle_id] = circle
        self._peer_circles.setdefault(owner_id, set()).add(circle_id)

        log.info("circle_created", name=name, owner=owner_id, id=circle_id)
        return circle

    def get_circle(self, circle_id: str) -> TrustedCircle | None:
        return self._circles.get(circle_id)

    def delete_circle(self, circle_id: str, by_peer: str = "") -> bool:
        """Loescht einen Circle (nur Owner)."""
        circle = self._circles.get(circle_id)
        if not circle:
            return False
        if not by_peer or circle.owner_id != by_peer:
            return False

        # Clean up peer associations
        for member_id in circle.members:
            if member_id in self._peer_circles:
                self._peer_circles[member_id].discard(circle_id)

        del self._circles[circle_id]
        log.info("circle_deleted", name=circle.name, id=circle_id)
        return True

    def list_circles(self, peer_id: str = "") -> list[TrustedCircle]:
        """List circles, optionally filtered by peer membership."""
        if not peer_id:
            return list(self._circles.values())
        circle_ids = self._peer_circles.get(peer_id, set())
        return [self._circles[cid] for cid in circle_ids if cid in self._circles]

    # ── Einladungen ──────────────────────────────────────────────

    def invite_to_circle(
        self,
        circle_id: str,
        inviter_id: str,
        invitee_id: str,
        **kwargs: Any,
    ) -> CircleInvite | None:
        """Create an invitation."""
        circle = self._circles.get(circle_id)
        if not circle:
            return None
        return circle.create_invite(inviter_id, invitee_id, **kwargs)

    def accept_invite(self, circle_id: str, invite_id: str) -> CircleMember | None:
        """Accept a circle invitation."""
        circle = self._circles.get(circle_id)
        if not circle:
            return None

        invite = circle.invites.get(invite_id)
        if not invite:
            return None

        # Max circle check
        peer_circles = self._peer_circles.get(invite.invitee_id, set())
        if len(peer_circles) >= self.MAX_CIRCLES_PER_PEER:
            return None

        member = circle.accept_invite(invite_id)
        if member:
            self._peer_circles.setdefault(invite.invitee_id, set()).add(circle_id)
        return member

    # ── Trust-Abfragen ───────────────────────────────────────────

    def is_in_shared_circle(self, peer_a: str, peer_b: str) -> bool:
        """Check if two peers share at least one common circle."""
        circles_a = self._peer_circles.get(peer_a, set())
        circles_b = self._peer_circles.get(peer_b, set())
        return bool(circles_a & circles_b)

    def shared_circles(self, peer_a: str, peer_b: str) -> list[str]:
        """Return shared circle IDs."""
        circles_a = self._peer_circles.get(peer_a, set())
        circles_b = self._peer_circles.get(peer_b, set())
        return list(circles_a & circles_b)

    def trust_score_for_package(
        self,
        package_id: str,
        publisher_id: str,
        requester_id: str,
    ) -> float:
        """Calculate trust score of a package based on circle membership.

        Returns:
            Basis-Score + Circle-Boost.
            Boost = CIRCLE_REPUTATION_BOOST pro gemeinsamem Circle.
        """
        base_score = 0.0

        # Circle-Boost: Publisher und Requester in gleichem Circle?
        shared = self.shared_circles(publisher_id, requester_id)
        circle_boost = len(shared) * self.CIRCLE_REPUTATION_BOOST

        # Kuratierungs-Boost: Ist der Skill in einem Circle approved?
        curation_boost = 0.0
        for circle_id in shared:
            circle = self._circles.get(circle_id)
            if circle:
                skill = circle.curated_skills.get(package_id)
                if skill and skill.is_approved:
                    curation_boost += 5.0  # Großer Bonus für kuratierte Skills

        total = base_score + circle_boost + curation_boost
        return total

    def filter_trusted_packages(
        self,
        package_ids: list[str],
        publisher_map: dict[str, str],
        requester_id: str,
        min_score: float = 0.0,
    ) -> list[tuple[str, float]]:
        """Filter packages by trust score.

        Args:
            package_ids: Liste von Paket-IDs.
            publisher_map: Mapping package_id → publisher_id.
            requester_id: Eigene Peer-ID.
            min_score: Mindest-Score fuer Ergebnisse.

        Returns:
            Sortierte Liste von (package_id, score), hoechster Score zuerst.
        """
        scored = []
        for pkg_id in package_ids:
            pub_id = publisher_map.get(pkg_id, "")
            score = self.trust_score_for_package(pkg_id, pub_id, requester_id)
            if score >= min_score:
                scored.append((pkg_id, score))

        return sorted(scored, key=lambda x: x[1], reverse=True)

    # ── Kuratierte Sammlungen ────────────────────────────────────

    def create_collection(
        self,
        name: str,
        maintainer_id: str,
        description: str = "",
        tags: list[str] | None = None,
        public: bool = False,
    ) -> CuratedCollection:
        """Create a curated collection."""
        collection_id = hashlib.sha256(f"col:{name}:{maintainer_id}".encode()).hexdigest()[:12]

        collection = CuratedCollection(
            collection_id=collection_id,
            name=name,
            description=description,
            maintainer_id=maintainer_id,
            tags=tags or [],
            public=public,
        )
        self._collections[collection_id] = collection
        log.info("collection_created", name=name, maintainer=maintainer_id)
        return collection

    def get_collection(self, collection_id: str) -> CuratedCollection | None:
        return self._collections.get(collection_id)

    def list_collections(self, public_only: bool = False) -> list[CuratedCollection]:
        """List all collections."""
        if public_only:
            return [c for c in self._collections.values() if c.public]
        return list(self._collections.values())

    def search_collections(self, query: str) -> list[CuratedCollection]:
        """Search collections by name, description, or tags."""
        query_lower = query.lower()
        return [
            c
            for c in self._collections.values()
            if (
                query_lower in c.name.lower()
                or query_lower in c.description.lower()
                or any(query_lower in t.lower() for t in c.tags)
            )
        ]

    # ── Statistiken ──────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        """Ecosystem statistics."""
        total_members = sum(c.member_count for c in self._circles.values())
        total_curated = sum(len(c.curated_skills) for c in self._circles.values())
        total_approved = sum(len(c.approved_skills()) for c in self._circles.values())

        return {
            "circles": len(self._circles),
            "total_members": total_members,
            "total_curated_skills": total_curated,
            "total_approved_skills": total_approved,
            "collections": len(self._collections),
            "unique_peers": len(self._peer_circles),
        }
