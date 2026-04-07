import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import java.time.Duration;

public class HomePage {
    private WebDriver driver;
    private static final By SEARCH_BOX = By.id("twotabsearchtextbox");
    private static final By SEARCH_BUTTON = By.id("nav-search-submit-button");

    public HomePage(WebDriver driver) {
        this.driver = driver;
    }

    // Method to verify the page is loaded
    public boolean isLoaded() {
        return driver.getTitle().contains("Amazon");
    }

    // Method to search for a term
    public SearchResultsPage searchFor(String searchTerm) {
        WebElement searchBox = new WebDriverWait(driver, Duration.ofSeconds(10))
                .until(ExpectedConditions.visibilityOfElementLocated(SEARCH_BOX));
        searchBox.sendKeys(searchTerm);

        WebElement searchButton = driver.findElement(SEARCH_BUTTON);
        searchButton.click();

        return new SearchResultsPage(driver);
    }
}