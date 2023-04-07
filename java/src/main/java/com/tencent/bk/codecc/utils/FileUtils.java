package com.tencent.bk.codecc.utils;

import com.tencent.bk.codecc.enums.OSType;
import org.apache.commons.compress.utils.Lists;
import org.apache.commons.io.FilenameUtils;
import org.apache.commons.io.IOUtils;
import org.apache.commons.lang3.StringUtils;
import org.omg.Messaging.SYNC_WITH_TRANSPORT;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.regex.Pattern;
import java.util.stream.Collectors;
import java.util.stream.Stream;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

public class FileUtils {

    /**
     * 获取PreCI路径
     *
     * @return
     */
    public static String getPreCIPath() {
        String path = "";
        if (Objects.nonNull(System.getProperty("preciDir"))) {
            path = System.getProperty("preciDir");
        } else {
            path = System.getProperty("user.home");
            if (path.endsWith(File.separator)) {
                path = path + "PreCi";
            } else {
                path = path + File.separator + "PreCi";
            }
        }
        return FileUtils.createPath(path);
    }

    /**
     * 解压zip
     *
     * @param file
     * @param destDir
     */
    public static void unzipFile(String file, String destDir) throws Exception {
        ZipFile zipFile = new ZipFile(file);
        if (Objects.nonNull(zipFile)) {
            Enumeration<? extends ZipEntry> entries = zipFile.entries();
            while (entries.hasMoreElements()) {
                ZipEntry entry = entries.nextElement();
                File entryDestination = new File(destDir, entry.getName());
                if (entry.isDirectory()) {
                    entryDestination.mkdirs();
                } else {
                    if (entryDestination.getParentFile() != null) {
                        entryDestination.getParentFile().mkdirs();
                    }
                    try (InputStream in = zipFile.getInputStream(entry);
                         OutputStream out = new FileOutputStream(entryDestination)) {
                        IOUtils.copy(in, out);
                    }
                }
            }
        }
    }

    public static String filePathChangeToInput(String filePath) {
        if (OSType.WINDOWS.equals(AgentEnv.getOS())) {
            if (filePath.startsWith("/")) {
                return filePath.replaceFirst(":", "").replace("\\", "/");
            } else {
                return "/" + filePath.replaceFirst(":", "").replace("\\", "/");
            }
        }

        return filePath;
    }

    public static String filePathChangeToOutput(String filePath) {
        if (OSType.WINDOWS.equals(AgentEnv.getOS())) {
            return filePath.substring(1).replaceFirst("/", ":/").replace("/", "\\");
        }

        return filePath;
    }

    /**
     * 获取系统对应的路径换行
     *
     * @param filePath
     * @return
     */
    public static String separatorsToSystem(String filePath) {
        if (OSType.WINDOWS.equals(AgentEnv.getOS())) {
            return FilenameUtils.separatorsToWindows(filePath);
        }

        return filePath;
    }

    /**
     * 搜索白名单绝对路径
     *
     * @param whitePath
     * @param scanPath
     * @return
     */
    public static List<String> traverseWhitePath(String whitePath, String scanPath, boolean isDockerEnable)
            throws Exception {
        List<String> whitePathList = Lists.newArrayList();
        if (whitePath.endsWith("/.*")) {
            whitePath = StringUtils.removeEnd(whitePath, "/.*");
        } else {
            if (whitePath.endsWith("/")) {
                whitePath = StringUtils.removeEnd(whitePath, "/");
            }
        }
        File file = new File(whitePath);
        if (file.exists()) {
            whitePathList.add(whitePath);
        } else {
            Stream<Path> walk = Files.walk(Paths.get(scanPath));
            if (walk != null) {
                List<Path> resultList = walk.filter(Files::isDirectory)
                        .collect(Collectors.toList());
                for (Path path : resultList) {
                    String filePath = path.toString().replace("\\", "/");
                    if (Pattern.matches(whitePath, filePath)) {
                        if (isDockerEnable) {
                            String subPath = filePathChangeToInput(path.toFile().getAbsolutePath());
                            if (!isSubPathForExistPath(subPath, whitePathList)) {
                                whitePathList.add(subPath);
                            }
                        } else {
                            String subPath = path.toFile().getAbsolutePath().replace("\\", "/");
                            if (!isSubPathForExistPath(subPath, whitePathList)) {
                                whitePathList.add(subPath);
                            }
                        }
                    }
                }
            }
        }
        return whitePathList;
    }

    public static List<String> walkPath(String scanPath) throws Exception {
        List<String> scanFiles = Lists.newArrayList();
        List<Path> resultList;
        Stream<Path> walk = Files.walk(Paths.get(scanPath));
        if (walk != null) {
            resultList = walk.filter(Files::isRegularFile)
                    .collect(Collectors.toList());
            for (Path path : resultList) {
                scanFiles.add(path.toFile().getAbsolutePath().replace("\\", "/"));
            }
        }
        return scanFiles;
    }

    public static void chmodPath(String path, boolean readable, boolean writable, boolean executable) throws Exception {
        for (String filePath : walkPath(path)) {
            if (Paths.get(filePath).toFile().isFile()) {
                Paths.get(filePath).toFile().setReadable(readable);
                Paths.get(filePath).toFile().setWritable(writable);
                Paths.get(filePath).toFile().setExecutable(executable);
            }
        }
    }

    /**
     * 保存内容到文件中
     *
     * @param filePath
     * @param content
     * @return
     */
    public static boolean saveContentToFile(String filePath, String content) {
        BufferedWriter bw = null;
        try {
            File file = new File(filePath);
            if (file.getParent() != null) {
                File parentPath = new File(file.getParent());
                if (!parentPath.exists()) {
                    parentPath.mkdirs();
                }
            }
            bw = new BufferedWriter(
                    new OutputStreamWriter(
                            new FileOutputStream(filePath),
                            StandardCharsets.UTF_8));
            bw.write(new String(content.getBytes(), StandardCharsets.UTF_8));
            file.setExecutable(true, false);
        } catch (IOException e) {
            System.out.println("saveContentToFile保存内容到文件中失败");
            return false;
        } finally {
            try {
                if (bw != null) {
                    bw.close();
                }
            } catch (IOException e) {
                System.out.println("saveContentToFile关闭文件流失败");
            }
        }
        return true;
    }

    public static String createPath(String path) {
        File pathFile = new File(path);
        if (!pathFile.exists()) {
            pathFile.mkdirs();
        }
        return path;
    }


    /**
     * 修改文件内容：字符串逐行替换
     *
     * @param file   待处理的文件
     * @param oldstr 需要替换的旧字符串
     * @param newStr 用于替换的新字符串
     */
    public static boolean modifyFileContent(File file, String oldstr, String newStr) {
        List<String> list = null;
        try {
            list = org.apache.commons.io.FileUtils.readLines(file, "UTF-8");
            for (int i = 0; i < list.size(); i++) {
                String temp = list.get(i).replaceAll(oldstr, newStr);
                list.remove(i);
                list.add(i, temp);
            }
            org.apache.commons.io.FileUtils.writeLines(file, "UTF-8", list, false);
        } catch (IOException e) {
            System.out.println("modifyFileContent修改文件内容失败");
        }
        return true;
    }

    /**
     * 修改文件内容：删除匹配字符串的行
     *
     * @param file 待处理的文件
     * @param str  需要删除的字符串
     */
    public static boolean deleteFileContentFromStr(File file, String str) {
        List<String> list = null;
        BufferedWriter out = null;
        try {
            List<String> newFileList = new ArrayList<>();
            list = org.apache.commons.io.FileUtils.readLines(file, "UTF-8");
            for (int i = 0; i < list.size(); i++) {
                if (list.get(i).contains(str)) {
                    continue;
                }
                newFileList.add(list.get(i));
            }
            out = new BufferedWriter(new FileWriter(file));
            out.write(StringUtils.join(newFileList, "\t\n"));
        } catch (IOException e) {
            System.out.println("deleteFileContentFromStr修改文件内容失败");
        } finally {
            if (out != null) {
                try {
                    out.close();
                } catch (IOException e) {
                    System.out.println("deleteFileContentFromStr关闭文件流失败");
                }
            }
        }
        return true;
    }

    /**
     * 修改文件内容：尾行插入内容
     *
     * @param file 待处理的文件
     * @param str  需要插入的字符串
     */
    public static boolean fileInsertContentForEndLine(File file, String str) {
        List<String> list = null;
        BufferedWriter out = null;
        try {
            list = org.apache.commons.io.FileUtils.readLines(file, "UTF-8");
            list.add(list.size(), str);
            //            org.apache.commons.io.FileUtils.writeLines(file, "UTF-8", list, false);
            out = new BufferedWriter(new FileWriter(file));
            out.write(StringUtils.join(list, "\t\n"));
        } catch (IOException e) {
            System.out.println("fileInsertContent修改文件内容失败");
        } finally {
            if (out != null) {
                try {
                    out.close();
                } catch (IOException e) {
                    System.out.println("fileInsertContent关闭文件流失败");
                }
            }
        }
        return true;
    }

    /**
     * 修改文件内容：尾行插入内容如果不存在的话。
     *
     * @param file 待处理的文件
     * @param strList  需要插入的字符串Lists
     */
    public static boolean fileInsertContentIfNotExist(File file, List<String> strList) {
        List<String> list = null;
        BufferedWriter out = null;
        try {
            if (!file.isFile()) {
                file.createNewFile();
            }
            boolean needUpdate = false;
            list = org.apache.commons.io.FileUtils.readLines(file, "UTF-8");
            for (String str: strList) {
                List<String> checkExist = list.stream().filter(it -> it.equals(str)).collect(Collectors.toList());
                if (checkExist.size() == 0) {
                    list.add(list.size(), str);
                    needUpdate = true;
                }
            }
            if (needUpdate) {
                out = new BufferedWriter(new FileWriter(file));
                out.write(StringUtils.join(list, "\n"));
            }
        } catch (IOException e) {
            e.printStackTrace();
        } finally {
            if (out != null) {
                try {
                    out.close();
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }
        }
        return true;
    }

    public static String getFileName(String filePath) {
        File file = new File(filePath);
        return file.getName();
    }

    public static boolean isFile(String filePath) {
        File file = new File(filePath);
        return file.isFile();
    }

    public static boolean isSkipFile(String path, List<String> skipPaths) {
        path = path.replace("\\", "/");
        for (String skiPath: skipPaths) {
            if (Pattern.matches(skiPath, path)) {
                return true;
            }
        }
        return false;
    }

    public static String isSpaceExistInPath(String path) {
        if (path.contains(" ") && !OSType.WINDOWS.equals(AgentEnv.getOS())) {
            return path.replace(" ", "\\ ");
        }
        return path;
    }

    /**
     * 检查该路径是否为已存在的路径列表中的子路径
     * @param subPath
     * @param pathList
     * @return
     */
    public static boolean isSubPathForExistPath(String subPath, List<String> pathList) {
        subPath = subPath.replace("\\", "/");
        for (String existPath: pathList) {
            if (subPath.contains(existPath)) {
                return true;
            }
        }
        return false;
    }

    /**
     * Gets the path of the JDK from the agent path.
     * @param agentPath the path where the agent is located
     * @return the path of the JDK
     */
    public static String jdkPathFromAgent(String agentPath) {
        String agentProperties = agentPath + File.separator + ".agent.properties";
        String jdkPath = "";
        if (Paths.get(agentProperties).toFile().exists()) {
            Properties properties = new Properties();
            BufferedReader bufferedReader = null;
            try {
                bufferedReader = new BufferedReader(new FileReader(agentProperties));
                properties.load(bufferedReader);
                if (properties.getProperty("devops.agent.jdk.dir.path") != null) {
                    jdkPath = properties.getProperty("devops.agent.jdk.dir.path");
                } else {
                    if (Paths.get(agentPath + File.separator + "jdk").toFile().exists()) {
                        jdkPath =  agentPath + File.separator + "jdk";
                    } else if (Paths.get(agentPath + File.separator + "jre").toFile().exists()) {
                        jdkPath =  agentPath + File.separator + "jre";
                    }
                }
            } catch (FileNotFoundException e) {
                e.printStackTrace();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }

        jdkPath += (AgentEnv.getOS() == OS.MACOS) ? "/Contents/Home/bin" : "/bin";


        return jdkPath;
    }
}
