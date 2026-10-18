//! Dependency-free domain types for the Crews & Gigs media-community prototype.
//! These types are a starting point for a future API; the current static site
//! does not persist records or run this crate in the browser.

/// The kind of post a member can publish to the network.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ListingKind {
    Member,
    Gig,
    Equipment,
    CommunityQuestion,
}

/// A broad discipline in the media and production community.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum MediaDiscipline {
    Music,
    LiveProduction,
    AudioVisual,
    Photography,
    Video,
    Design,
    Editing,
    Production,
    Other,
}

/// A public-facing listing summary. A production service can replace these
/// static string slices with owned, validated database records.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct MediaListing {
    pub slug: &'static str,
    pub title: &'static str,
    pub kind: ListingKind,
    pub discipline: MediaDiscipline,
    pub location: &'static str,
}

/// Representative starter records matching the front-end prototype.
pub const FEATURED_LISTINGS: [MediaListing; 4] = [
    MediaListing { slug: "sade-sound", title: "Sade Okonkwo", kind: ListingKind::Member, discipline: MediaDiscipline::AudioVisual, location: "Lagos, Nigeria" },
    MediaListing { slug: "touring-drummer", title: "Touring drummer wanted", kind: ListingKind::Gig, discipline: MediaDiscipline::Music, location: "Accra, Ghana" },
    MediaListing { slug: "aputure-300d", title: "Aputure 300D II kit", kind: ListingKind::Equipment, discipline: MediaDiscipline::Video, location: "Lagos, Nigeria" },
    MediaListing { slug: "crew-rates", title: "How do you price a small crew?", kind: ListingKind::CommunityQuestion, discipline: MediaDiscipline::Production, location: "Community" },
];

/// Find featured posts of one kind, retaining their editorial order.
pub fn listings_of_kind(kind: ListingKind) -> Vec<MediaListing> {
    FEATURED_LISTINGS.iter().copied().filter(|listing| listing.kind == kind).collect()
}

/// Lightweight email syntax check for request validation. Real account
/// creation must additionally verify the address and validate server-side.
pub fn is_valid_email(email: &str) -> bool {
    let email = email.trim();
    if email.len() > 254 || email.chars().any(char::is_whitespace) { return false; }
    if email.matches('@').count() != 1 { return false; }
    let Some((local, domain)) = email.split_once('@') else { return false; };
    let allowed_local = |ch: char| ch.is_ascii_alphanumeric() || ".!#$%&'*+-/=?^_`{|}~".contains(ch);
    let labels: Vec<&str> = domain.split('.').collect();
    !local.is_empty()
        && local.len() <= 64
        && !local.starts_with('.')
        && !local.ends_with('.')
        && !local.contains("..")
        && local.chars().all(allowed_local)
        && domain.len() <= 253
        && labels.len() >= 2
        && labels.iter().all(|label| {
            !label.is_empty()
                && label.len() <= 63
                && !label.starts_with('-')
                && !label.ends_with('-')
                && label.chars().all(|ch| ch.is_ascii_alphanumeric() || ch == '-')
        })
        && labels.last().map_or(false, |label| label.len() >= 2)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn featured_listings_cover_people_gigs_gear_and_help() {
        for kind in [ListingKind::Member, ListingKind::Gig, ListingKind::Equipment, ListingKind::CommunityQuestion] {
            assert_eq!(listings_of_kind(kind).len(), 1);
        }
    }

    #[test]
    fn email_check_accepts_normal_addresses() {
        assert!(is_valid_email("hello@example.com"));
        assert!(is_valid_email("  folu+crew@example.co.uk  "));
    }

    #[test]
    fn email_check_rejects_malformed_addresses() {
        for email in ["", "hello", "@example.com", "hello@localhost", "a b@example.com", "a..b@example.com", "a@b@c.com", ".a@example.com", "a@-example.com", "a@example-.com", "a@x.y"] {
            assert!(!is_valid_email(email), "should reject {email}");
        }
    }
}
