# Branch Protection Setup

This document explains how to configure GitHub branch protection to require passing tests before merging PRs.

## Required Configuration

To enforce test requirements on pull requests, configure branch protection rules in your GitHub repository:

### Step 1: Navigate to Branch Protection Settings

1. Go to your repository on GitHub
2. Click **Settings** → **Branches**
3. Under **Branch protection rules**, click **Add rule**

### Step 2: Configure Protection for `main` Branch

Set the following options:

#### Branch name pattern
```
main
```

#### Protection Rules

**Require a pull request before merging:**
- ✅ Enable this option
- Require approvals: 1 (or more, based on your team policy)

**Require status checks to pass before merging:**
- ✅ Enable this option
- ✅ Require branches to be up to date before merging
- **Add required status checks:**
  - Search for and select: `test` (this is the job name from `.github/workflows/test.yml`)

**Additional Recommended Settings:**
- ✅ Require conversation resolution before merging
- ✅ Do not allow bypassing the above settings (prevents force pushes)

### Step 3: Save Rules

Click **Create** or **Save changes**

## What This Accomplishes

With these settings:

1. **PRs are required** - Direct pushes to `main` are blocked
2. **Tests must pass** - The `test` workflow must complete successfully
3. **Up-to-date branches** - PR branch must be rebased/merged with latest `main`
4. **Code review** - At least 1 approval required before merging

## Test Workflow Details

The test workflow (`.github/workflows/test.yml`) will:

- ✅ Run on every pull request to `main` or `develop`
- ✅ Run all 189 unit tests
- ✅ Validate Dual-LLM security architecture
- ✅ Test all specialized agents (support, sales, billing, quarantined)
- ✅ Verify graph routing and conversation flows
- ✅ Block merge if any test fails

## Testing the Workflow

To verify the setup works:

```bash
# Create a test branch
git checkout -b test/verify-ci

# Make a small change
echo "# Test CI" >> README.md

# Commit and push
git add README.md
git commit -m "test: Verify CI/CD pipeline"
git push origin test/verify-ci

# Create a PR on GitHub
# You should see the "Test Suite" check running
```

## Manual Test Execution

To run tests locally before pushing:

```bash
# Run all tests
./run_tests.sh all

# Run with coverage
./run_tests.sh coverage

# Run only critical security tests
./run_tests.sh critical
```

## Troubleshooting

**Test check not appearing:**
- Ensure the workflow file is in `.github/workflows/test.yml`
- Check that your PR modifies files in `src/` or `tests/`
- Verify the workflow is enabled in **Settings** → **Actions**

**Test check failing:**
- Click "Details" on the failed check to see logs
- Run `./run_tests.sh all` locally to reproduce
- Fix failing tests before pushing again

**Status check not required:**
- Verify branch protection is configured for the correct branch
- Ensure the status check name matches the job name: `test`
- Wait a few minutes for GitHub to recognize the workflow
