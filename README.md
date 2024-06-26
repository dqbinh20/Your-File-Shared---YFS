# Your-File_Shared---YFS

## Giới thiệu

YFS là chương trình quản lý file phi tập trung sử dụng thuật toán SES multicast để điều phối truy cập và cập nhật dữ liệu. Hệ thống bao gồm 5 máy, mỗi máy đóng vai trò như một nút lưu trữ và cung cấp thư mục riêng cho các máy khác mount.

## Chức năng chính

- Truy cập và cập nhật dữ liệu đồng thời: Sử dụng thuật toán SES multicast để đảm bảo thứ tự thực hiện các lệnh đọc/ghi một cách hiệu quả.
- Ghi chép nhật ký: Lưu trữ trạng thái timestamp và vector process vào file log.txt để theo dõi hoạt động hệ thống.

## Hướng dẫn sử dụng

### Bước 1: Khởi chạy YFS

- Khởi chạy 5 file YFS.py trên cùng một máy.
- Nhập tên process tương ứng cho mỗi máy: A, B, C, D, E.
- Mỗi máy sẽ tạo thư mục và file.txt mang tên process. Ví dụ: process A: /A/file.txt.

### Bước 2: Thực hiện các lệnh

- Đọc file: R [Tên máy]
- Ghi file: W [Tên máy] [Nội dung]

### Ví dụ:

#

- Đọc file từ máy A: `R A `

- Ghi nội dung "Hello, YFS!" vào file của máy B: `W B Hello, YFS!`

### Ghi chú

- Các lệnh đọc/ghi được thực hiện đồng thời trên tất cả các máy.
- Thứ tự thực hiện các lệnh được đảm bảo bởi thuật toán SES multicast.
- Trạng thái timestamp và vector process được ghi vào log.txt để theo dõi hoạt động hệ thống.
