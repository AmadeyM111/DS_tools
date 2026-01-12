package com.parse.service;

import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;

import java.io.FileWriter;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;

public class KoapParser {

    private static final String BASE_URL = "https://www.zakonrf.info/koap/";
    private static final int TARGET_ARTICLES = 200;
    private static final Duration REQUEST_TIMEOUT = Duration.ofSeconds(30);
    private static final int DELAY_BETWEEN_REQUESTS_MS = 2000;

    private static final HttpClient httpClient = HttpClient.newBuilder()
            .connectTimeout(REQUEST_TIMEOUT)
            .version(HttpClient.Version.HTTP_1_1)
            .followRedirects(HttpClient.Redirect.NORMAL)
            .build();

    private static final HttpRequest.Builder defaultRequestBuilder = HttpRequest.newBuilder()
            .header("User-Agent", "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36")
            .header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7")
            .header("Accept-Language", "ru,en-US;q=0.9,en;q=0.8")
            .header("Accept-Encoding", "gzip")
            .header("Upgrade-Insecure-Requests", "1")
            .timeout(REQUEST_TIMEOUT);

    private static String fetchWithRetry(String urlString, int maxRetries) throws IOException, InterruptedException {
        URI uri = URI.create(urlString);
        HttpRequest request = defaultRequestBuilder
                .uri(uri)
                .GET()
                .build();

        int attempt = 0;
        IOException lastException = null;

        while (attempt < maxRetries) {
            try {
                HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
                if (response.statusCode() == 200) {
                    return response.body();
                } else if (response.statusCode() == 404) {
                    System.out.println("Статья не найдена: " + urlString);
                    return null;
                } else {
                    throw new IOException("HTTP " + response.statusCode() + " for URL: " + urlString);
                }
            } catch (IOException e) {
                lastException = e;
                attempt++;
                if (attempt < maxRetries) {
                    Thread.sleep(2000 * attempt);
                }
            }
        }
        throw lastException;
    }

    private static String getFullTextHtml(String articleUrl) throws IOException, InterruptedException {
        return fetchWithRetry(articleUrl, 3);
    }

    private static String parseArticleText(Document doc) {
        Element content = doc.selectFirst(".article-text, .content, .post-content, #content, .text, .article-content");
        
        if (content != null) {
            return content.text().trim();
        }
        
        Element h1 = doc.selectFirst("h1");
        if (h1 != null) {
            StringBuilder textBuilder = new StringBuilder();
            textBuilder.append(h1.text()).append("\n");

            Element current = h1.nextElementSibling();
            while (current != null && !current.tagName().equals("h1")) {
                if (current.tagName().equals("p") || 
                    current.tagName().equals("div") ||
                    current.hasClass("article") || 
                    current.hasClass("content")) {
                    String text = current.text().trim();
                    if (!text.isEmpty() && !text.matches("^©.*") && !text.matches("^Источник:.*")) {
                        textBuilder.append(text).append("\n");
                    }
                }
                current = current.nextElementSibling();
            }
            return textBuilder.toString().trim();
        }
        
        doc.select("nav, header, footer, aside, .menu, .sidebar, .footer, .header").remove();
        return doc.body().text().trim();
    }

    private static String parseArticleTitle(Document doc) {
        Element title = doc.selectFirst("h1");
        if (title != null) {
            return title.text().trim();
        }
        
        title = doc.selectFirst(".article-title, .post-title, .title");
        if (title != null) {
            return title.text().trim();
        }
        
        Element metaTitle = doc.selectFirst("meta[property=og:title]");
        if (metaTitle != null) {
            return metaTitle.attr("content").trim();
        }
        
        return "Статья";
    }

    private static String parseArticleSection(Document doc, String articleNum) {
        try {
            String[] parts = articleNum.split("\\.");
            int chapter = Integer.parseInt(parts[0]);
            
            if (chapter >= 1 && chapter <= 4) {
                return "Раздел I. Общие положения";
            } else if (chapter >= 5 && chapter <= 21) {
                return "Раздел II. Особенная часть";
            } else if (chapter >= 22 && chapter <= 30) {
                return "Раздел III. Судьи, органы, должностные лица, уполномоченные рассматривать дела об административных правонарушениях";
            } else if (chapter >= 31 && chapter <= 32) {
                return "Раздел IV. Производство по делам об административных правонарушениях";
            } else {
                return "Другие разделы";
            }
        } catch (NumberFormatException e) {
            return "Общие положения";
        }
    }

    private static List<Article> collectArticles(int targetCount) throws IOException, InterruptedException {
        System.out.println("Начинаем сбор статей...");
        List<Article> dataset = new ArrayList<>();
        
        for (int chapter = 1; chapter <= 32; chapter++) {
            for (int articleNum = 1; articleNum <= 50; articleNum++) {
                if (dataset.size() >= targetCount) {
                    return dataset;
                }
                
                String articleUrl = BASE_URL + chapter + "." + articleNum + "/";
                System.out.println("Парсим: " + articleUrl + " (статей собрано: " + dataset.size() + ")");
                
                try {
                    String htmlContent = getFullTextHtml(articleUrl);
                    
                    if (htmlContent == null) {
                        continue;
                    }
                    
                    Document doc = Jsoup.parse(htmlContent);
                    
                    String title = parseArticleTitle(doc);
                    String text = parseArticleText(doc);
                    String section = parseArticleSection(doc, chapter + "." + articleNum);
                    
                    if (text.length() > 100 && !text.toLowerCase().contains("страница не найдена")) {
                        dataset.add(new Article(title, text, section));
                        System.out.println("  ✓ Добавлена: " + title);
                    } else {
                        System.out.println("  ✗ Пропущена (мало текста или ошибка): " + title);
                    }
                    
                    Thread.sleep(DELAY_BETWEEN_REQUESTS_MS);
                    
                } catch (Exception e) {
                    System.err.println("Ошибка при парсинге " + articleUrl + ": " + e.getMessage());
                }
            }
        }
        
        return dataset;
    }

    private static void saveToCsv(List<Article> dataset) throws IOException {
    	try (FileWriter cleanWriter = new FileWriter("koap_zakonrf_dataset_CLEAN.csv", StandardCharsets.UTF_8)) {
            cleanWriter.write("\uFEFF"); 
            cleanWriter.write("\"title\",\"section\",\"text\"\n");
            for (Article article : dataset) {
                String escapedTitle = article.title.replace("\"", "\"\"");
                String escapedSection = article.section.replace("\"", "\"\"");
                String escapedText = article.text.replace("\"", "\"\"");
                cleanWriter.write(String.format("\"%s\",\"%s\",\"%s\"\n",
                        escapedTitle, escapedSection, escapedText));
            }
        }

        try (FileWriter statsWriter = new FileWriter("koap_zakonrf_dataset_STATS.csv", StandardCharsets.UTF_8)) {
            statsWriter.write("\uFEFF"); 
            statsWriter.write("\"title\",\"section\",\"char_count\",\"word_count\"\n");
            for (Article article : dataset) {
                int charCount = article.text.length();
                int wordCount = article.text.isEmpty() ? 0 : article.text.split("\\s+").length;
                String escapedTitle = article.title.replace("\"", "\"\"");
                String escapedSection = article.section.replace("\"", "\"\"");
                statsWriter.write(String.format("\"%s\",\"%s\",%d,%d\n",
                        escapedTitle, escapedSection, charCount, wordCount));
            }
        

        }

        System.out.println("\n" + "=".repeat(50));
        System.out.println(" ГОТОВО! ");
        System.out.println("=".repeat(50));
        System.out.println("1. Файл для обучения: koap_zakonrf_dataset_CLEAN.csv");
        System.out.println("2. Файл статистики:   koap_zakonrf_dataset_STATS.csv");
        System.out.println("-".repeat(50));
        System.out.println("Всего статей: " + dataset.size());
        long avgChars = (long) dataset.stream().mapToInt(a -> a.text.length()).average().orElse(0);
        System.out.println("Средняя длина: " + (int) avgChars + " символов");
        
        System.out.println("\nПримеры собранных статей:");
        for (int i = 0; i < Math.min(3, dataset.size()); i++) {
            Article a = dataset.get(i);
            System.out.println((i+1) + ". " + a.title + " (" + a.text.length() + " символов)");
        }
    }

    static class Article {
        String title;
        String text;
        String section;

        Article(String title, String text, String section) {
            this.title = title;
            this.text = text;
            this.section = section;
        }
    }

    public static void main(String[] args) {
        try {
            System.out.println("Тестируем парсинг одной статьи...");
            String testUrl = BASE_URL + "1.1/";
            String htmlContent = getFullTextHtml(testUrl);
            
            if (htmlContent != null) {
                Document doc = Jsoup.parse(htmlContent);
                System.out.println("Заголовок: " + parseArticleTitle(doc));
                System.out.println("Текст (первые 200 символов): " + 
                        parseArticleText(doc).substring(0, Math.min(200, parseArticleText(doc).length())) + "...");
                
                List<Article> dataset = collectArticles(TARGET_ARTICLES);
                
                if (!dataset.isEmpty()) {
                    saveToCsv(dataset);
                } else {
                    System.err.println("Не удалось собрать ни одной статьи!");
                }
            } else {
                System.err.println("Не удалось получить тестовую статью!");
            }

        } catch (Exception e) {
            System.err.println("Ошибка выполнения: " + e.getMessage());
            e.printStackTrace();
        }
    }
}