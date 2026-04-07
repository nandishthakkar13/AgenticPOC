import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import java.time.Duration;

public class SearchResultsPage {
    private WebDriver driver;
    private static final By FIRST_RESULT = By.cssSelector(".s-main-slot .s-result-item");

    public SearchResultsPage(WebDriver driver) {
        this.driver = driver;
    }

    // Method to verify the page is loaded
    public boolean isLoaded() {
        return driver.getTitle().contains("laptops");
    }

    // Method to click on the first search result
    public void clickFirstResult() {
        WebElement firstResult = new WebDriverWait(driver, Duration.ofSeconds(10))
                .until(ExpectedConditions.elementToBeClickable(FIRST_RESULT));
        firstResult.click();
    }
}