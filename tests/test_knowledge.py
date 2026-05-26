"""Tests for the knowledge package."""

from pathlib import Path

import pytest
import yaml

from knowledge.store import KnowledgeStore
from knowledge.skill_composer import SkillComposer


class TestKnowledgeStructure:
    """Tests for knowledge directory structure."""

    def test_knowledge_package_importable(self) -> None:
        """Test that knowledge package can be imported."""
        import knowledge
        assert knowledge is not None

    def test_store_importable(self) -> None:
        """Test that knowledge.store can be imported."""
        from knowledge import store
        assert store is not None

    def test_knowledge_store_class_exists(self) -> None:
        """Test that KnowledgeStore class exists."""
        from knowledge.store import KnowledgeStore
        assert KnowledgeStore is not None

    def test_knowledge_store_instantiation(self, tmp_knowledge: Path) -> None:
        """Test that KnowledgeStore can be instantiated."""
        ks = KnowledgeStore(str(tmp_knowledge))
        assert ks.knowledge_root == tmp_knowledge

    def test_skill_composer_importable(self) -> None:
        """Test that knowledge.skill_composer can be imported."""
        from knowledge.skill_composer import SkillComposer
        assert SkillComposer is not None


class TestKnowledgeStoreRules:
    """Tests for KnowledgeStore rule operations."""

    def test_add_manual_rule(self, tmp_knowledge: Path) -> None:
        """Test adding a manual rule."""
        ks = KnowledgeStore(str(tmp_knowledge))
        rule = {
            "name": "test_rule",
            "description": "A test rule",
            "content": "Always test your code",
            "tags": ["testing", "quality"],
            "source": "manual",
        }
        ks.add_rule(rule, learned=False)
        rules = ks.get_rules()
        assert len(rules) == 1
        assert rules[0]["name"] == "test_rule"

    def test_add_learned_rule(self, tmp_knowledge: Path) -> None:
        """Test adding a learned rule."""
        ks = KnowledgeStore(str(tmp_knowledge))
        rule = {
            "name": "learned_pattern",
            "description": "A learned pattern",
            "content": "Smaller functions are better",
            "tags": ["learned", "refactoring"],
            "source": "reflector",
        }
        ks.add_rule(rule, learned=True)
        # Check it was stored in learned/
        assert (tmp_knowledge / "rules" / "learned" / "learned_pattern.yaml").exists()

    def test_get_rules_no_filter(self, tmp_knowledge: Path) -> None:
        """Test getting all rules without filter."""
        ks = KnowledgeStore(str(tmp_knowledge))
        ks.add_rule({"name": "r1", "tags": ["a"], "description": "", "content": "", "source": ""})
        ks.add_rule({"name": "r2", "tags": ["b"], "description": "", "content": "", "source": ""})
        rules = ks.get_rules()
        assert len(rules) == 2

    def test_get_rules_with_filter(self, tmp_knowledge: Path) -> None:
        """Test getting rules filtered by tags."""
        ks = KnowledgeStore(str(tmp_knowledge))
        ks.add_rule({"name": "r1", "tags": ["testing"], "description": "", "content": "", "source": ""})
        ks.add_rule({"name": "r2", "tags": ["quality"], "description": "", "content": "", "source": ""})
        rules = ks.get_rules(filter_tags=["testing"])
        assert len(rules) == 1
        assert rules[0]["name"] == "r1"


class TestKnowledgeStoreSkills:
    """Tests for KnowledgeStore skill operations."""

    def test_add_skill(self, tmp_knowledge: Path) -> None:
        """Test adding a skill."""
        ks = KnowledgeStore(str(tmp_knowledge))
        ks.add_skill("grill-me", "Interview preparation skill", tags=["interview"])
        skills = ks.list_skills()
        assert len(skills) == 1
        assert skills[0]["name"] == "grill-me"

    def test_get_skill(self, tmp_knowledge: Path) -> None:
        """Test getting a skill by name."""
        ks = KnowledgeStore(str(tmp_knowledge))
        ks.add_skill("test-skill", "A test skill", tags=["test"], path="test-skill")
        skill = ks.get_skill("test-skill")
        assert skill["name"] == "test-skill"
        assert skill["description"] == "A test skill"

    def test_get_nonexistent_skill(self, tmp_knowledge: Path) -> None:
        """Test that getting a nonexistent skill raises KeyError."""
        ks = KnowledgeStore(str(tmp_knowledge))
        with pytest.raises(KeyError, match="Skill not found"):
            ks.get_skill("nonexistent")

    def test_list_skills_with_tags(self, tmp_knowledge: Path) -> None:
        """Test listing skills filtered by tags."""
        ks = KnowledgeStore(str(tmp_knowledge))
        ks.add_skill("s1", "Skill 1", tags=["code"])
        ks.add_skill("s2", "Skill 2", tags=["review"])
        ks.add_skill("s3", "Skill 3", tags=["code", "review"])
        skills = ks.list_skills(tags=["code"])
        assert len(skills) == 2

    def test_list_skills_no_filter(self, tmp_knowledge: Path) -> None:
        """Test listing all skills."""
        ks = KnowledgeStore(str(tmp_knowledge))
        ks.add_skill("s1", "Skill 1")
        ks.add_skill("s2", "Skill 2")
        skills = ks.list_skills()
        assert len(skills) == 2


class TestKnowledgeStorePatterns:
    """Tests for KnowledgeStore pattern operations."""

    def test_add_pattern(self, tmp_knowledge: Path) -> None:
        """Test adding a pattern."""
        ks = KnowledgeStore(str(tmp_knowledge))
        pattern = {
            "name": "singleton",
            "description": "Singleton pattern",
            "content": "class Singleton: ...",
            "tags": ["design-pattern"],
            "context": "When you need a single instance",
        }
        ks.add_pattern(pattern)
        patterns = ks.get_patterns()
        assert len(patterns) == 1
        assert patterns[0]["name"] == "singleton"

    def test_get_patterns_with_filter(self, tmp_knowledge: Path) -> None:
        """Test getting patterns filtered by tags."""
        ks = KnowledgeStore(str(tmp_knowledge))
        ks.add_pattern({"name": "p1", "tags": ["arch"], "description": "", "content": "", "context": ""})
        ks.add_pattern({"name": "p2", "tags": ["code"], "description": "", "content": "", "context": ""})
        patterns = ks.get_patterns(filter_tags=["arch"])
        assert len(patterns) == 1
        assert patterns[0]["name"] == "p1"


class TestKnowledgeStoreRebuildIndex:
    """Tests for rebuild_index."""

    def test_rebuild_rules_index(self, tmp_knowledge: Path) -> None:
        """Test rebuilding the rules index."""
        ks = KnowledgeStore(str(tmp_knowledge))
        # Add a rule
        ks.add_rule({"name": "rule1", "tags": ["t1"], "description": "D", "content": "C", "source": "s"})
        # Clear the index manually
        ks._save_index(ks.rules_dir, {"items": []})
        assert len(ks.get_rules()) == 0
        # Rebuild
        ks.rebuild_index("rules")
        rules = ks.get_rules()
        assert len(rules) == 1

    def test_rebuild_patterns_index(self, tmp_knowledge: Path) -> None:
        """Test rebuilding the patterns index."""
        ks = KnowledgeStore(str(tmp_knowledge))
        ks.add_pattern({"name": "pat1", "tags": ["t1"], "description": "D", "content": "C", "context": ""})
        ks._save_index(ks.patterns_dir, {"items": []})
        assert len(ks.get_patterns()) == 0
        ks.rebuild_index("patterns")
        patterns = ks.get_patterns()
        assert len(patterns) == 1

    def test_rebuild_invalid_category(self, tmp_knowledge: Path) -> None:
        """Test that invalid category raises ValueError."""
        ks = KnowledgeStore(str(tmp_knowledge))
        with pytest.raises(ValueError, match="Invalid category"):
            ks.rebuild_index("invalid")


class TestSkillComposer:
    """Tests for SkillComposer."""

    def test_compose_valid_skills(self, tmp_knowledge: Path) -> None:
        """Test composing multiple skills."""
        ks = KnowledgeStore(str(tmp_knowledge))
        # Create skill directories with SKILL.md
        skill1_dir = tmp_knowledge / "skills" / "skill1"
        skill1_dir.mkdir(parents=True)
        (skill1_dir / "SKILL.md").write_text("# Skill 1 content")

        skill2_dir = tmp_knowledge / "skills" / "skill2"
        skill2_dir.mkdir(parents=True)
        (skill2_dir / "SKILL.md").write_text("# Skill 2 content")

        ks.add_skill("skill1", "First skill", path="skill1")
        ks.add_skill("skill2", "Second skill", path="skill2")

        sc = SkillComposer(ks)
        result = sc.compose(["skill1", "skill2"])
        assert "## Skill: skill1" in result
        assert "## Skill: skill2" in result
        assert "# Skill 1 content" in result
        assert "# Skill 2 content" in result

    def test_compose_missing_skill(self, tmp_knowledge: Path) -> None:
        """Test that composing with missing skill raises ValueError."""
        ks = KnowledgeStore(str(tmp_knowledge))
        sc = SkillComposer(ks)
        with pytest.raises(ValueError, match="Composition validation failed"):
            sc.compose(["nonexistent"])

    def test_validate_composition_empty(self, tmp_knowledge: Path) -> None:
        """Test validate_composition with empty list."""
        ks = KnowledgeStore(str(tmp_knowledge))
        sc = SkillComposer(ks)
        issues = sc.validate_composition([])
        assert len(issues) > 0
        assert "No skills specified" in issues[0]

    def test_validate_composition_valid(self, tmp_knowledge: Path) -> None:
        """Test validate_composition with valid skills."""
        ks = KnowledgeStore(str(tmp_knowledge))
        ks.add_skill("valid_skill", "A valid skill")
        sc = SkillComposer(ks)
        issues = sc.validate_composition(["valid_skill"])
        assert issues == []

    def test_validate_composition_missing(self, tmp_knowledge: Path) -> None:
        """Test validate_composition with missing skills."""
        ks = KnowledgeStore(str(tmp_knowledge))
        sc = SkillComposer(ks)
        issues = sc.validate_composition(["missing1", "missing2"])
        assert len(issues) == 2

    def test_resolve_order(self, tmp_knowledge: Path) -> None:
        """Test that resolve_order returns as-is."""
        ks = KnowledgeStore(str(tmp_knowledge))
        sc = SkillComposer(ks)
        result = sc.resolve_order(["a", "b", "c"])
        assert result == ["a", "b", "c"]

    def test_get_skill_content(self, tmp_knowledge: Path) -> None:
        """Test getting individual skill content."""
        ks = KnowledgeStore(str(tmp_knowledge))
        skill_dir = tmp_knowledge / "skills" / "test_skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("Test content here")
        ks.add_skill("test_skill", "Test skill", path="test_skill")

        sc = SkillComposer(ks)
        content = sc.get_skill_content("test_skill")
        assert content == "Test content here"

    def test_get_skill_content_not_found(self, tmp_knowledge: Path) -> None:
        """Test getting content for a skill without SKILL.md raises error."""
        ks = KnowledgeStore(str(tmp_knowledge))
        ks.add_skill("missing_skill", "Missing", path="missing_path")
        sc = SkillComposer(ks)
        with pytest.raises(FileNotFoundError):
            sc.get_skill_content("missing_skill")


class TestKnowledgeFiles:
    """Tests for knowledge directory files."""

    def test_rules_index_exists(self, kernel_root: Path) -> None:
        """Test that rules/_index.yaml exists and is valid."""
        path = kernel_root / "knowledge" / "rules" / "_index.yaml"
        assert path.exists()
        data = yaml.safe_load(path.read_text())
        assert "items" in data

    def test_skills_index_exists(self, kernel_root: Path) -> None:
        """Test that skills/_index.yaml exists and is valid."""
        path = kernel_root / "knowledge" / "skills" / "_index.yaml"
        assert path.exists()
        data = yaml.safe_load(path.read_text())
        assert "items" in data

    def test_patterns_index_exists(self, kernel_root: Path) -> None:
        """Test that patterns/_index.yaml exists and is valid."""
        path = kernel_root / "knowledge" / "patterns" / "_index.yaml"
        assert path.exists()
        data = yaml.safe_load(path.read_text())
        assert "items" in data

    def test_rules_manual_dir_exists(self, kernel_root: Path) -> None:
        """Test that rules/manual/ directory exists."""
        assert (kernel_root / "knowledge" / "rules" / "manual").is_dir()

    def test_rules_learned_dir_exists(self, kernel_root: Path) -> None:
        """Test that rules/learned/ directory exists."""
        assert (kernel_root / "knowledge" / "rules" / "learned").is_dir()

    def test_patterns_dir_exists(self, kernel_root: Path) -> None:
        """Test that patterns/ directory exists."""
        assert (kernel_root / "knowledge" / "patterns").is_dir()
