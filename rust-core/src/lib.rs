//! Domain helpers for the Foluso portfolio. This crate is intentionally
//! dependency-free and can be reused by a future Rust API or static-site build.

/// A portfolio discipline used to group and filter selected work.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Discipline {
    Development,
    Ai,
    Motion,
    Design,
}

/// A concise project record suitable for a portfolio index or API response.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Project {
    pub slug: &'static str,
    pub title: &'static str,
    pub discipline: Discipline,
    pub year: u16,
}

/// Curated case studies shown on the portfolio.
pub const PROJECTS: [Project; 4] = [
    Project { slug: "atlas", title: "Atlas — Find your own way", discipline: Discipline::Development, year: 2025 },
    Project { slug: "soma", title: "Sōma — Your thought partner", discipline: Discipline::Ai, year: 2025 },
    Project { slug: "keep-going", title: "Keep Going — Motion study", discipline: Discipline::Motion, year: 2025 },
    Project { slug: "form-feeling", title: "Form follows feeling", discipline: Discipline::Design, year: 2025 },
];

/// Return projects for a discipline, preserving the curated display order.
pub fn projects_in(discipline: Discipline) -> Vec<Project> {
    PROJECTS.iter().copied().filter(|project| project.discipline == discipline).collect()
}

/// A minimal contact-form check, suitable for client-side/API validation parity.
pub fn is_valid_email(email: &str) -> bool {
    let email = email.trim();
    if email.len() > 254 || email.chars().any(char::is_whitespace) { return false; }
    let Some((local, domain)) = email.split_once('@') else { return false; };
    !local.is_empty()
        && local.len() <= 64
        && domain.contains('.')
        && !domain.starts_with('.')
        && !domain.ends_with('.')
        && !domain.contains("..")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn each_discipline_has_a_curated_project() {
        for discipline in [Discipline::Development, Discipline::Ai, Discipline::Motion, Discipline::Design] {
            assert_eq!(projects_in(discipline).len(), 1);
        }
    }

    #[test]
    fn email_validation_accepts_normal_addresses() {
        assert!(is_valid_email("hello@foluso.dev"));
        assert!(is_valid_email("  foluso+work@example.co.uk  "));
    }

    #[test]
    fn email_validation_rejects_malformed_addresses() {
        for email in ["", "hello", "@example.com", "hello@localhost", "a b@example.com", "a..b@example.com"] {
            assert!(!is_valid_email(email), "should reject {email}");
        }
    }
}
