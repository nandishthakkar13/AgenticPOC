import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.AfterMethod;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Test;

public class AmazonLaptopSearchTest {
    private WebDriver driver;

    @BeforeMethod
    public void setUp() {
        // Set up ChromeDriver
        System.setProperty("webdriver.chrome.driver", "path/to/chromedriver");
        driver = new ChromeDriver();
        driver.manage().window().maximize();
    }

    @Test
    public void testAmazonLaptopSearch() {
        // Navigate to Amazon homepage
        driver.get("https://www.amazon.com");
        HomePage homePage = new HomePage(driver);
        Assert.assertTrue(homePage.isLoaded(), "Home page is not loaded");

        // Search for laptops
        SearchResultsPage searchResultsPage = homePage.searchFor("laptops");
        Assert.assertTrue(searchResultsPage.isLoaded(), "Search results page is not loaded");

        // Click on the first search result
        searchResultsPage.clickFirstResult();
        // Optionally, you can add more assertions here to verify the product page
    }

    @AfterMethod
    public void tearDown() {
        // Quit the driver
        if (driver != null) {
            driver.quit();
        }
    }
}