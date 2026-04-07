Here's the complete Selenium WebDriver test using the Page Object Model (POM) design pattern for the given scenario:

```java
// FILE: WikipediaHomePage.java
package pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import java.time.Duration;

// Page Object class for Wikipedia Home Page
public class WikipediaHomePage {
    private WebDriver driver;
    private WebDriverWait wait;

    // Locators for elements on the Wikipedia home page
    private static final By SEARCH_BOX = By.id("searchInput");
    private static final By SEARCH_BUTTON = By.xpath("//button[@type='submit']");

    // Constructor to initialize WebDriver and WebDriverWait
    public WikipediaHomePage(WebDriver driver) {
        this.driver = driver;
        this.wait = new WebDriverWait(driver, Duration.ofSeconds(10));
    }

    // Method to verify the page is loaded
    public boolean isLoaded() {
        return wait.until(ExpectedConditions.visibilityOfElementLocated(SEARCH_BOX)).isDisplayed();
    }

    // Method to perform a search
    public WikipediaSearchResultsPage searchFor(String query) {
        wait.until(ExpectedConditions.visibilityOfElementLocated(SEARCH_BOX)).sendKeys(query);
        wait.until(ExpectedConditions.elementToBeClickable(SEARCH_BUTTON)).click();
        return new WikipediaSearchResultsPage(driver);
    }
}
```

```java
// FILE: WikipediaSearchResultsPage.java
package pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import java.time.Duration;

// Page Object class for Wikipedia Search Results Page
public class WikipediaSearchResultsPage {
    private WebDriver driver;
    private WebDriverWait wait;

    // Constructor to initialize WebDriver and WebDriverWait
    public WikipediaSearchResultsPage(WebDriver driver) {
        this.driver = driver;
        this.wait = new WebDriverWait(driver, Duration.ofSeconds(10));
    }

    // Method to verify the page title
    public boolean isTitleCorrect(String expectedTitle) {
        return wait.until(ExpectedConditions.titleContains(expectedTitle));
    }
}
```

```java
// FILE: WikipediaArticleVerificationTest.java
package tests;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.AfterMethod;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Test;
import pages.WikipediaHomePage;
import pages.WikipediaSearchResultsPage;

// Test class for Wikipedia Article Verification
public class WikipediaArticleVerificationTest {
    private WebDriver driver;

    // Setup method to initialize WebDriver
    @BeforeMethod
    public void setUp() {
        // Set the path to the chromedriver executable
        System.setProperty("webdriver.chrome.driver", "path/to/chromedriver");
        driver = new ChromeDriver();
        driver.manage().window().maximize();
    }

    // Test method for the scenario
    @Test
    public void testWikipediaArticleVerification() {
        // Step 1: Open the Wikipedia main page
        driver.get("https://www.wikipedia.org");
        WikipediaHomePage homePage = new WikipediaHomePage(driver);
        Assert.assertTrue(homePage.isLoaded(), "Wikipedia home page is not loaded.");

        // Step 2: Enter 'Python programming language' in the search field
        WikipediaSearchResultsPage resultsPage = homePage.searchFor("Python programming language");

        // Step 3: Verify that the resulting page title contains the expected text
        Assert.assertTrue(resultsPage.isTitleCorrect("Python (programming language)"),
                "The page title does not contain the expected text.");
    }

    // Teardown method to quit WebDriver
    @AfterMethod
    public void tearDown() {
        if (driver != null) {
            driver.quit();
        }
    }
}
```

### Explanation:
- **WikipediaHomePage.java**: This class represents the Wikipedia home page. It contains locators for the search box and button, methods to perform a search, and a method to verify the page is loaded.
- **WikipediaSearchResultsPage.java**: This class represents the search results page. It contains a method to verify the page title.
- **WikipediaArticleVerificationTest.java**: This test class uses TestNG annotations to set up and tear down the WebDriver. It executes the test scenario by navigating to Wikipedia, performing a search, and verifying the page title.